from django.db import models

# 1. Danh mục sản phẩm
class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="Tên danh mục")
    def __str__(self):
        return self.name

# 2. Sản phẩm
class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="Danh mục")
    name = models.CharField(max_length=200, verbose_name="Tên sản phẩm")
    barcode = models.CharField(max_length=50, blank=True, null=True, verbose_name="Mã vạch")
    price = models.IntegerField(verbose_name="Giá bán (VND)")
    cost_price = models.IntegerField(verbose_name="Giá nhập (VND)", default=0)
    stock = models.IntegerField(verbose_name="Số lượng tồn kho")

    def __str__(self):
        return self.name

# THÊM MỚI 3: Khách hàng
class Customer(models.Model):
    name = models.CharField(max_length=150, verbose_name="Tên khách hàng")
    phone = models.CharField(max_length=15, unique=True, verbose_name="Số điện thoại")
    address = models.CharField(max_length=255, blank=True, null=True, verbose_name="Địa chỉ")
    birth_year = models.IntegerField(blank=True, null=True, verbose_name="Năm sinh")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tham gia")

    def __str__(self):
        return f"{self.name} - {self.phone}"

# 4. Đơn hàng (Hóa đơn bán ra)
class Order(models.Model):
    # THÊM TRƯỜNG NÀY: Liên kết tới khách hàng (để null nếu là khách lẻ)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, blank=True, null=True, verbose_name="Khách hàng")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Thời gian tạo")
    total_amount = models.IntegerField(verbose_name="Tổng tiền (VND)", default=0)

    def __str__(self):
        return f"Đơn hàng #{self.id} - {self.created_at.strftime('%d/%m/%Y %H:%M')}"

# 5. Chi tiết đơn hàng
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    price = models.IntegerField(verbose_name="Giá bán lúc mua")
    # THÊM TRƯỜNG NÀY:
    cost_price = models.IntegerField(verbose_name="Giá nhập lúc mua", default=0) 

    def __str__(self):
        return f"{self.product.name} (x{self.quantity})"
