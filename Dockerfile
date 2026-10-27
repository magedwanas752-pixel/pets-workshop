FROM node:22-bookworm-slim AS client-build

WORKDIR /app/client
COPY app/client/package.json app/client/package-lock.json ./
RUN npm ci
COPY app/client/ ./
RUN npm run build

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY app/server/requirements.txt /app/server/requirements.txt
RUN python -m pip install --no-cache-dir -r /app/server/requirements.txt
COPY app/server/ /app/server/
COPY --from=client-build /app/client/dist/ /app/client/dist/
COPY app/scripts/start-render.sh /app/start-render.sh
RUN chmod 755 /app/start-render.sh

EXPOSE 10000
CMD ["/app/start-render.sh"]
