class Cart:
    def __init__(self):
        self.items = {}
    def add_item(self, prod_id):
        self.items[prod_id] = self.items.get(prod_id, 0) + 1
    def remove_item(self, prod_id):
        if prod_id in self.items:
            self.items[prod_id] -= 1
            if self.items[prod_id] <= 0:
                del self.items[prod_id]
    def get_items(self):
        return dict(self.items)

cart = Cart()
