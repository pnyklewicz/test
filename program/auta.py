import requests

short_link = "ZMgDmc5s"
key = "70bfe8312839213262efb4a547bc5a1c"
token = "06454b032c2551fe84d5d971f74d616692386b10c2739d7e204fd615af653de4"

url = f"https://api.trello.com/1/boards/{short_link}?key={key}&token={token}"

response = requests.get(url)

if response.status_code == 200:
    board_data = response.json()
    print(board_data)
else:
    print(f"Błąd: {response.status_code}")
