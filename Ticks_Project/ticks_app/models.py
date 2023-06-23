from django.db import models
from django.db.models import F
from datetime import datetime, timedelta
from django.contrib.auth.models import User

# Create your models here.
class Balance(models.Model):
    acc_type = models.CharField(max_length=30)
    acc_name = models.CharField(max_length=30)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    initial_bal = models.FloatField(default = 0)
    in_bal = models.FloatField(default = 0)
    out_bal = models.FloatField(default = 0)
    close_bal = models.FloatField(default = 0)
    strategy = models.CharField(max_length=150)
    trans_date = models.DateTimeField(null=True, blank=True)

    @classmethod
    def newAcc(self,acc_type,acc_name,user,amount):
        el = Balance.objects.create(user=user)
        el.acc_type = acc_type
        el.acc_name = acc_name
        el.initial_bal = amount
        el.trans_date = datetime.now()
        el.save()

    @classmethod
    def initialBal(self,acc_name,user,amount):
        self.objects.filter(acc_name=acc_name,user=user).update(initial_bal=F('initial_bal') + amount)

    @classmethod   
    def inBal(self,acc_result,user,amount):
        self.objects.filter(acc_name=acc_result,user=user).update(in_bal=F("in_bal") + amount)

    @classmethod
    def final_inBal(self,acc_result,user):
        self.objects.filter(acc_name=acc_result,user=user).update(close_bal=F("initial_bal") + F("in_bal")-F("out_bal"))
    
    @classmethod   
    def outBal(self,acc_source,user,amount):
        self.objects.filter(acc_name=acc_source,user=user).update(out_bal=F('out_bal') + amount)

    @classmethod
    def final_outBal(self,acc_source,user):
        self.objects.filter(acc_name=acc_source,user=user).update(close_bal=F("initial_bal") + F("in_bal")-F("out_bal"))

    @classmethod
    def delAcc(self,acc_name,user):
        self.objects.filter(acc_name=acc_name,user=user).delete()


    @classmethod
    def resetBal(self,user):
        self.objects.filter(user=user).update(initial_bal=F("close_bal"))
        self.objects.filter(user=user).update(in_bal=0)
        self.objects.filter(user=user).update(in_out=0)
            

        

    




class Transactions(models.Model):
    items = models.CharField(max_length=50)
    amount = models.FloatField(default=0)
    acc_source = models.CharField(max_length=30)
    acc_result = models.CharField(max_length=30)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    trans_date = models.DateTimeField(null=True, blank=True)

    @classmethod
    def loadTrans(self,acc_source,acc_result,user,amount,items):
        el = Transactions.objects.create(user=user)
        el.items = items
        el.acc_source = acc_source
        el.acc_result = acc_result
        el.amount = amount
        el.trans_date = datetime.now()
        el.save()


class Capacity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    savings = models.FloatField(default=0)
    income = models.FloatField(default=0)
    start_date = models.IntegerField(default=0) #start of month e.g 25
    end_date = models.IntegerField(default=0) #end of month
    spend_rate = models.FloatField(default=0) #Average spend rate, To be stored on Transaction once a month

    @classmethod
    def capInstanceCreate(self,user,start_day):
        el = Capacity.objects.create(user=user)
        el.start_date = start_day
        el.save()

    @classmethod
    def savingIncomeCap(self,user,savings,income):
        self.objects.filter(user=user).update(savings=savings,income=income)
    




