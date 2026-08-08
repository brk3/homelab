docker run -d \
  --name=qbittorrent \
  -e PUID=1000 \
  -e PGID=1000 \
  -e TZ=Etc/UTC \
  -e WEBUI_PORT=8080 \
  -p 8080:8080 \
  -p 6881:6881 \
  -p 6881:6881/udp \
  -v /home/pbourke/qbittorrent-config:/config \
  -v /home/pbourke/torrents:/downloads \
  --restart unless-stopped \
  lscr.io/linuxserver/qbittorrent:latest
