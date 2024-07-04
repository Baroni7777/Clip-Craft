FROM python:3.11

WORKDIR /app

COPY requirements.txt /app/

RUN pip install -r requirements.txt

# Install ImageMagick, ffmpeg, and dependencies
RUN apt-get update && \
    apt-get install -y --fix-missing imagemagick ffmpeg && \
    apt-get clean

# Create fonts directory
RUN mkdir -p /usr/share/fonts/truetype/custom

# Copy all font files from the 'fonts' directory on your host to the container
COPY fonts/* /usr/share/fonts/truetype/custom/

# Update the font cache
RUN fc-cache -f -v

# Verify fonts are installed
RUN fc-list | grep -i "Agency\|Arial\|Harlow\|Tahoma\|Trebuchet"

COPY . /app/

EXPOSE 8000

CMD ["fastapi", "run"]
