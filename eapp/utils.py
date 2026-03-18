def stats_cart(cart):
    total_quantity, total_amount = 0, 0
    game_quantity, phone_quantity = 0, 0

    if cart:
        for c in cart.values():
            qty = c['quantity']
            price = c['price']
            card_type = c.get('card_type')

            total_quantity += qty
            total_amount += qty * price

            if card_type == 'game':
                game_quantity += qty
            elif card_type == 'phone':
                phone_quantity += qty

    return {
        'total_quantity': total_quantity,
        'total_amount': total_amount,
        'game_quantity': game_quantity,
        'phone_quantity': phone_quantity
    }