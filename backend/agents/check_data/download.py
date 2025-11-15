import http.client
import time
import json

conn = http.client.HTTPSConnection("www.528btc.com")
payload = ''
headers = {
  'accept': 'application/json, text/javascript, */*; q=0.01',
  'accept-language': 'zh-CN,zh;q=0.9',
  'content-length': '0',
  'origin': 'https://www.528btc.com',
  'priority': 'u=1, i',
  'referer': 'https://www.528btc.com/coin/3008.html',
  'sec-ch-ua': '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
  'sec-ch-ua-mobile': '?0',
  'sec-ch-ua-platform': '"Windows"',
  'sec-fetch-dest': 'empty',
  'sec-fetch-mode': 'cors',
  'sec-fetch-site': 'same-origin',
  'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
  'x-requested-with': 'XMLHttpRequest',
  'Cookie': '__cf_bm=Be7yMJCDK5qAWP9xtTVuLMnjOmCP00yMdwotp84BDxw-1762495008-1.0.1.1-4HAQHgQUFniUEg0n.jx9GIMkZqE48yEEGIVf4Z8HqC8Z6xH6OkS7R6K01iBlLHOqe4a6xJfCk2BxarR2oevvcIRkJW.0YiKqZDgUesvXWwo'
}
symbols = ["BTC","BNB","ETH","SOL","XRP","ADA","DOGE","MATIC","ATOM","ETC"]
for symbol in symbols:
    all_data = []
    for i in range(1, 10):
        conn.request("POST", f"/e/extend/api/index.php?m=kline&c=coin&slug=bitcoin&id=1&sortByDate=true&sortByDateRule=false&symbol={symbol}&type=2&limit=300&page={i}", payload, headers)
        res = conn.getresponse()
        data = res.read()
        data = data.decode("utf-8")
        all_data.extend(json.loads(data))
        time.sleep(2)
    # 按 t 升序排序
    all_data.sort(key=lambda x: x["T"])
    # 写入json文件    
    json.dump(all_data, open(f"{symbol}.json", "w", encoding="utf-8"))
    print(f"下载{symbol}完成")
    