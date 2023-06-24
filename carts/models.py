from django.db import models
from store.models import Product
from accounts.models import Account
# Create your models here.
class Cart(models.Model):
    cart_id=models.CharField(max_length=250,blank=True)
    date_added=models.DateField(auto_now_add=True)
    
    
    def __str__(self):
        return self.cart_id
    
class CartItem(models.Model):
    product=models.ForeignKey(Product,on_delete=models.CASCADE,default=None,blank=True,null=True)
    cart=models.ForeignKey(Cart,on_delete=models.CASCADE,default=None,blank=True,null=True)
    variation=models.ManyToManyField('Variation',blank=True)
    quantity=models.IntegerField()
    is_active=models.BooleanField(default=True)
    user=models.ForeignKey(Account,on_delete=models.CASCADE,null=True,blank=True)
    
    def sub_total(self):
        return self.product.price*self.quantity
    
    def __unicode__(self):
        return self.product
    
variation_category_choices=(
    ('color','color'),
    ('size','size'),
)
    
class VariationManager(models.Manager):
    def colors(self):
        return super(VariationManager,self).filter(variation_category='color',is_active=True)
    def sizes(self):
        return super(VariationManager,self).filter(variation_category='size',is_active=True)
    
class Variation(models.Model):
    product=models.ForeignKey(Product,on_delete=models.CASCADE)
    variation_category=models.CharField(max_length=100,choices=variation_category_choices)
    variation_value=models.CharField(max_length=100)
    is_active=models.BooleanField(default=True)
    created_date=models.DateTimeField(auto_now=True)
    
    objects=VariationManager()
    
    def __unicode__(self):
        return self.product
    
    def __str__(self):
        return self.variation_value