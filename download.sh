set -x playlist $argv[1]
mkdir -p input
mkdir -p work
mkdir -p results
yt-dlp --write-auto-sub --skip-download --sub-lang en -o "input/%(title)s.%(ext)s" $playlist
