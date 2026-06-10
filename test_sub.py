from app.services.subscription_service import get_all_subscriptions, get_subscription_by_id

def test_subscriptions():
    print("Testing get_all_subscriptions...")
    subs = get_all_subscriptions()
    for sub in subs:
        print(f"ID: {sub.id}, Name: {sub.name}, Price Count: {len(sub.prices)}")
    
    print("\nTesting get_subscription_by_id...")
    basic = get_subscription_by_id("package_basic")
    print(f"Basic Package: {basic.name}, Tokens: {basic.services.tokens_per_bot_per_month}")

    default = get_subscription_by_id("non_existent")
    print(f"Default Package (on invalid ID): {default.name}")

if __name__ == "__main__":
    test_subscriptions()
