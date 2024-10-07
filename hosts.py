
def load_hosts():
    with open("hosts", 'r') as f:
        return [line.strip() for line in f.readlines()]

hosts = load_hosts()
