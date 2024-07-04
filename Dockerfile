FROM python:3.11

WORKDIR /app

COPY requirements.txt /app/

RUN pip install -r requirements.txt

# Install ImageMagick, ffmpeg, and dependencies
RUN apt-get update && \
    apt-get install -y --fix-missing imagemagick ffmpeg && \
    apt-get clean

COPY . /app/

EXPOSE 8000

CMD ["fastapi", "run"]
