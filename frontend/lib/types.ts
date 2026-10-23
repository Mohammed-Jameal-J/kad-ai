// Mirrors the FastAPI response schemas (backend/app/schemas). Money is integer paise.

export type CategoryRef = { id: number; slug: string; name: string };

export type Category = CategoryRef & {
  description: string;
  image_path: string;
  product_count: number;
  children: Category[];
};

export type Product = {
  id: number;
  slug: string;
  name: string;
  description: string;
  category: CategoryRef;
  price_paise: number;
  original_price_paise: number | null;
  unit: string;
  stock_quantity: number;
  image_path: string;
  rating: number;
  is_featured: boolean;
  is_bestseller: boolean;
  in_stock: boolean;
  discount_percent: number;
};

export type Nutrition = {
  food_description: string;
  source_name: string;
  source_id: string | null;
  source_url: string | null;
  serving_size_g: number;
  energy_kcal: number | null;
  protein_g: number | null;
  carbohydrate_g: number | null;
  fiber_g: number | null;
  sugars_g: number | null;
  fat_g: number | null;
  vitamin_c_mg: number | null;
  potassium_mg: number | null;
};

export type ProductDetail = Product & { nutrition: Nutrition | null; price_note: string };

export type ProductPage = {
  items: Product[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  price_note: string;
};

export type CartLine = {
  id: number;
  product: Pick<Product, "id" | "slug" | "name" | "unit" | "image_path" | "stock_quantity">;
  quantity: number;
  unit_price_paise: number;
  line_total_paise: number;
  available: boolean;
};

export type Cart = {
  cart_id: string | null;
  items: CartLine[];
  item_count: number;
  subtotal_paise: number;
  currency: string;
  price_note: string;
};

// --- Assistant (backend/app/schemas/assistant.py) ---------------------------------------------

export type ChatTurn = { role: "user" | "assistant"; content: string };

export type BasketLine = {
  product_id: number;
  name: string;
  unit: string;
  quantity: number;
  unit_price_paise: number;
  line_total_paise: number;
};

export type PendingAction = {
  type: "add_to_cart";
  items: { product_id: number; quantity: number }[];
  total_paise: number;
  summary: string;
};

export type ChatResponse = {
  reply: string;
  intent: string;
  products: Product[];
  basket: { lines: BasketLine[]; total_paise: number; budget_paise: number | null; remaining_paise: number | null } | null;
  pending_action: PendingAction | null;
  nutrition: { product_id: number; product_name: string; nutrition: Nutrition | null }[];
  notes: string[];
  parser: string;
  writer: string;
  duration_ms: number;
  price_note: string;
};

// --- Orders (backend/app/schemas/order.py) --------------------------------------------------------

export type DeliverySlot = "08-12" | "12-16" | "16-20";

export type CheckoutDetails = {
  customer_name: string;
  phone: string;
  address: string;
  delivery_slot: DeliverySlot;
};

export type Order = {
  id: string;
  customer_name: string;
  delivery_slot: DeliverySlot;
  payment_method: string;
  status: string;
  total_paise: number;
  items: { product_id: number; product_name: string; unit: string; quantity: number; unit_price_paise: number; line_total_paise: number }[];
  notice: string;
  price_note: string;
};

export type SortOption = "relevance" | "price_asc" | "price_desc" | "name_asc" | "name_desc" | "newest";

export type ProductFilters = {
  q?: string;
  category?: string;
  min_price?: number;
  max_price?: number;
  in_stock?: boolean;
  featured?: boolean;
  bestseller?: boolean;
  on_sale?: boolean;
  sort?: SortOption;
  page?: number;
  page_size?: number;
};
