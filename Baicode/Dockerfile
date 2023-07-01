FROM python:3.8

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

# 设置环境变量来启用调试模式
ENV FLASK_ENV=development

EXPOSE 56789

CMD ["flask", "run", "--host=0.0.0.0", "--port=56789"]
