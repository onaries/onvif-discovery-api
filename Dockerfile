FROM python:3.11
ENV API_PORT=8000
RUN mkdir -p /share
RUN pip install --upgrade pip
ADD requirements.txt .
RUN pip install -r requirements.txt
ADD . .
EXPOSE 8000
VOLUME [ "/share" ]
CMD ["python", "main.py"]
