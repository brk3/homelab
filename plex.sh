docker run -d \
  --name=plex \
  --net=host \
  -e PUID=1000 \
  -e PGID=1000 \
  -e TZ=Etc/UTC \
  -e VERSION=docker \
  -v /home/pbourke/plex-config:/config \
  -v /home/pbourke/torrents/torrents:/torrents \
  --restart unless-stopped \
  lscr.io/linuxserver/plex:latest
