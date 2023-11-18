import re
import uuid
import random
import socket
from urllib.parse import unquote
from urllib3.util import parse_url


SYMBOLS = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-_"


def rand_string(size, base):
    return "".join(SYMBOLS[random.randint(0, base - 1)] for _ in range(size))


def find_tag_value(xml, tag):
    regex = re.compile(rf"<[^/>]*{tag}[^>]*>([^<]+)")

    m = re.search(regex, xml)
    if m and len(m.groups()) != 2:
        return m.group(1)
    return ""


def discovery_streaming_devices():
    conn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    conn.bind(("0.0.0.0", 0))  # Bind to any available local port

    random_uuid = str(uuid.uuid4())
    msg = f"""
    <?xml version="1.0" ?>
    <s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope">
        <s:Header xmlns:a="http://schemas.xmlsoap.org/ws/2004/08/addressing">
            <a:Action>http://schemas.xmlsoap.org/ws/2005/04/discovery/Probe</a:Action>
            <a:MessageID>urn:uuid:{random_uuid}</a:MessageID>
            <a:To>urn:schemas-xmlsoap-org:ws:2005:04:discovery</a:To>
        </s:Header>
        <s:Body>
            <d:Probe xmlns:d="http://schemas.xmlsoap.org/ws/2005/04/discovery">
                <d:Types />
                <d:Scopes />
            </d:Probe>
        </s:Body>
    </s:Envelope>
    """

    addr = "239.255.255.250"
    port = 3702

    conn.sendto(msg.encode(), (addr, port))
    conn.settimeout(5)

    devices = []

    while True:
        try:
            data, addr = conn.recvfrom(8192)
        except socket.timeout:
            break

        decoded_data = data.decode()
        if not "onvif" in decoded_data:
            continue

        url = find_tag_value(decoded_data, "XAddrs")
        if not url:
            continue

        if url.startswith("http://0.0.0.0"):
            url = "http://" + addr[0] + url[14:]

        url = url.split(" ")[0]

        try:
            p_url = parse_url(url)
        except Exception as e:
            print(e)
            continue

        scopes = find_tag_value(decoded_data, "Scopes")
        hardware = (
            scopes[scopes.find("hardware") + 9 :].split(" ")[0]
            if "hardware" in scopes
            else ""
        )
        mac = scopes[scopes.find("MAC") + 4 :].split(" ")[0] if "MAC" in scopes else ""
        name = (
            scopes[scopes.find("name") + 5 :].split(" ")[0] if "name" in scopes else ""
        )
        profile = [
            scope.split("/")[-1]
            for scope in scopes.split(" ")
            if scope.startswith("onvif://www.onvif.org/Profile")
        ]
        metadata_version = find_tag_value(decoded_data, "MetadataVersion")
        device = {
            "name": unquote(name),
            "hardware": unquote(hardware),
            "ip": f"{p_url.host}:{p_url.port if p_url.port else 80}",
            "xaddrs": url,
            "mac": unquote(mac),
            "profile": profile,
            "metadata_version": unquote(metadata_version),
        }
        devices.append(device)

    conn.close()
    return devices


def extract_ip():
    st = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        st.connect(("10.255.255.255", 1))
        IP = st.getsockname()[0]
    except Exception:
        IP = "127.0.0.1"
    finally:
        st.close()
    return IP


if __name__ == "__main__":
    print(discovery_streaming_devices())
