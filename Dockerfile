# syntax=docker/dockerfile:1
FROM python:3.12.10

RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

WORKDIR /app

# copy and install Python reqs
COPY app/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# download Qdrant binary
RUN wget https://github.com/qdrant/qdrant/releases/download/v1.11.5/qdrant-x86_64-unknown-linux-gnu.tar.gz \
    && tar -xzf qdrant-x86_64-unknown-linux-gnu.tar.gz \
    && mv qdrant /home/user/.local/bin/qdrant \
    && rm qdrant-x86_64-unknown-linux-gnu.tar.gz

COPY --chown=user . /app

RUN chmod +x start.sh

CMD ["./start.sh"]
