# mediathekbot

This bot watches [https://mediathekviewweb.de/](https://mediathekviewweb.de/) for new entries.

## usage

```bash
python3 -m venv venv
source ./venv/bin/activate
pip3 install -r requirements.txt
# your telegram token (from @BotFather)
echo "$TOKEN" > token.txt
./bin/mediathekbot -b
```
