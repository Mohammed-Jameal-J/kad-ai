# Importing every model here registers all tables on Base.metadata before create_all().
from app.models.cart import Cart, CartItem
from app.models.catalog import Category, NutritionReference, Product
from app.models.order import Order, OrderItem
from app.models.user import ContactMessage, NewsletterSubscriber, User, UserSession

__all__ = [
    "Cart", "CartItem", "Category", "ContactMessage", "NewsletterSubscriber", "NutritionReference", "Order", "OrderItem",
    "Product", "User", "UserSession",
]
