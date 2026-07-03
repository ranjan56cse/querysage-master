FROM python:3.12-slim

WORKDIR /code

COPY ./streamlit_app.py ./

RUN pip install --no-cache-dir \
    streamlit \
    httpx \
    pandas \
    plotly \
    google-auth

EXPOSE 8501

CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
