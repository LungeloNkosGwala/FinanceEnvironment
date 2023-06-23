from django.shortcuts import render
from django.contrib.auth import authenticate, login,logout
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse
from django.contrib.auth.forms import UserCreationForm
from ticks_app.models import Transactions,Balance,Capacity
from django.contrib import messages
from django.contrib.auth.models import User
from datetime import datetime, timedelta
from django.utils import timezone
import pandas as pd
import pytz
from django.db.models import Sum
import plotly.graph_objects as go
import plotly.express as px
from django.db.models import Q


def index(request):
    return render(request,"ticks_app/index.html")

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return render(request,"ticks_app/index.html")
    else:
        form = UserCreationForm()
    return render(request, "ticks_app/register.html",{"form":form})

def user_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get('password')

        user = authenticate(username=username, password=password)

        if user:
            if user.is_active:
                login(request,user)
                user_d = request.user
                #return HttpResponseRedirect(reverse("index"))
                return render(request,"ticks_app/index.html",{"user_d":user_d})
            else:
                return HttpResponse("Account Not active")
        else:
            print("Someone tried to login and failed")
            return HttpResponse("Invalid login details supplied")
    else:
        return render(request,'ticks_app/login.html')
    
def user_logout(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def createAccount(request):
    user_d = request.user

    all_acc = Balance.objects.all().filter(user=user_d.id)

    if "acc_name" in request.POST and "acc_type" in request.POST and "amount" in request.POST and "submit" in request.POST:
        acc_name = request.POST['acc_name']
        main = request.POST['main']
        acc_type = request.POST['acc_type']
        amount = request.POST['amount']
        user = User.objects.get(id=user_d.id)

        Balance.newAcc(acc_type,acc_name,user,amount)
        messages.success(request,"Account successfully created")

    elif "select" in request.POST and "delete" in request.POST:
        acc_name = request.POST['select']
        user = User.objects.get(id=user_d.id)

        Balance.delAcc(acc_name,user)

        messages.warning(request,"Account Delete sucessfully")

        
    return render(request, "ticks_app/accounts/createAccount.html",{"all_acc":all_acc})

def transactions(request):
    user_d = request.user

    user_trans = Transactions.objects.all().filter(user=user_d.id)

    verify = Balance.objects.filter(user=user_d.id).first()
    if verify is None:
        all_acc = []
    else:
        all = Balance.objects.filter(user=user_d.id).values("acc_name")
        all_acc = []
        for i in all:
            all_acc.append(i.get("acc_name"))
        
    all_items = ["Grocery","Airtime/Data","Insurance","Inter-AccountTransfer","CreditAccount","Takeouts","VehicleFinance",
            "Home/Rent","Water/Electricity","Entertainment","Petrol","Clothes","BankCharges","Emergency",
            "VehicleOthers","Health/Medicine","Support","HomeOthers","Income"]
    
    if "submit" in request.POST and "amount" in request.POST:
        amount = request.POST['amount']
        items = request.POST['items']
        acc_source = request.POST['source']
        acc_result = request.POST['result']
        print(amount)
        if (int(amount) == 0 or amount == "" or amount==" "):
            pass
        else:
            user = User.objects.get(id=user_d.id)
            Transactions.loadTrans(acc_source,acc_result,user,amount,items)
            
            if acc_source == "Market":
                pass
            else:
                cl = Balance.objects.get(user=user,acc_name=acc_source)
                if (cl.acc_type == "Short-Term_Debt" or cl.acc_type == "Long-Term_Debt"):
                    amount = float(amount)*-1
                else:
                    pass
                Balance.outBal(acc_source,user,amount)
                Balance.final_outBal(acc_source,user)

            if acc_result == "Market":
                pass
            else:
                cl = Balance.objects.get(user=user,acc_name=acc_result)
                if (cl.acc_type == "Short-Term_Debt" or cl.acc_type == "Long-Term_Debt"):
                    amount = float(amount)*-1
                else:
                    pass
                Balance.inBal(acc_result,user,amount)
                Balance.final_inBal(acc_result,user)
            


            messages.success(request,"Transactions loaded successfully")
            context = {"all_acc":all_acc,"all_items":all_items,"user_trans":user_trans}
            return render(request, "ticks_app/accounts/transactions.html",context)
        
    elif "search" in request.POST:
        amount = request.POST['amount']
        items = request.POST['items']
        acc_source = request.POST['source']
        acc_result = request.POST['result']
        type_search = request.POST['type_search']
        from_date = request.POST['from']
        to_date = request.POST['to']
        user = User.objects.get(id=user_d.id)

        print(from_date)

        today = timezone.now()
        if from_date == "" and to_date == "":
            n = 30
            na = 1
            from_date = today - timedelta(days=n)
            from_date = from_date.strftime("%Y-%m-%d %H:%M:%S.%f%z")
            to_date = today + timedelta(days=na)
            to_date = to_date.strftime("%Y-%m-%d %H:%M:%S.%f%z")
        elif from_date == "":
            n = 30
            from_date = today - timedelta(days=n)
            from_date = from_date.strftime("%Y-%m-%d %H:%M:%S.%f%z")
        elif to_date == "":
            n = 1
            to_date = today + timedelta(days=n)
            to_date = to_date.strftime("%Y-%m-%d %H:%M:%S.%f%z")
        else:
            pass

        if type_search == "all_search":
            user_trans = Transactions.objects.all().filter(trans_date__range=[from_date,to_date],user=user)

        elif type_search == "select_search":
            user_trans = Transactions.objects.all().filter(trans_date__range=[from_date,to_date],
                                                       items=items,
                                                       acc_source = acc_source,
                                                       acc_result=acc_result,
                                                       user=user)
        elif type_search == "item_search":
            user_trans = Transactions.objects.all().filter(trans_date__range=[from_date,to_date],
                                                       items=items,
                                                       user=user)
        elif type_search == "source_search":
            user_trans = Transactions.objects.all().filter(trans_date__range=[from_date,to_date],
                                                       acc_source = acc_source,
                                                       user=user)
        elif type_search == "result_search":
            user_trans = Transactions.objects.all().filter(trans_date__range=[from_date,to_date],
                                                       acc_result=acc_result,
                                                       user=user)  
        else:
            pass


        context = {"all_acc":all_acc,"all_items":all_items,"user_trans":user_trans}
        return render(request, "ticks_app/accounts/transactions.html",context)
    
    elif "delete" in request.POST and 'clear' in request.POST:
        clear_id = request.POST['clear']
        user = User.objects.get(id=user_d.id)

        el = Transactions.objects.get(id=clear_id)

        
        amount = float(el.amount)*-1
        
        if el.acc_source == "Market":
            pass
        else:
            cl = Balance.objects.get(user=user,acc_name=el.acc_source)
            if (cl.acc_type == "Short-Term_Debt" or cl.acc_type == "Long-Term_Debt"):
                amount = float(amount)*-1
            else:
                pass
            acc_source = el.acc_source
            Balance.outBal(acc_source,user,amount)
            Balance.final_outBal(acc_source,user)

        if el.acc_result == "Market":
            pass
        else:
            cl = Balance.objects.get(user=user,acc_name=el.acc_result)
            if (cl.acc_type == "Short-Term_Debt" or cl.acc_type == "Long-Term_Debt"):
                amount = float(amount)*-1
            else:
                pass
            acc_result = el.acc_result
            Balance.inBal(acc_result,user,amount)
            Balance.final_inBal(acc_result,user)

        Transactions.objects.filter(id=clear_id).delete()

        messages.success(request,"Transactions deleted successfully")
        context = {"all_acc":all_acc,"all_items":all_items,"user_trans":user_trans}
        return render(request, "ticks_app/accounts/transactions.html",context)
    
    else:
        context = {"all_acc":all_acc,"all_items":all_items,"user_trans":user_trans}
        return render(request, "ticks_app/accounts/transactions.html",context)

    context = {"all_acc":all_acc,"all_items":all_items,"user_trans":user_trans}
    return render(request, "ticks_app/accounts/transactions.html",context)



def balance(request):
    user_d = request.user
    stt = Balance.objects.all().filter(user=user_d.id,acc_type="Short-Term_Transactions")
    ltt = Balance.objects.all().filter(user=user_d.id,acc_type="Long-Term_Transactions")
    std = Balance.objects.all().filter(user=user_d.id,acc_type="Short-Term_Debt")
    ltd = Balance.objects.all().filter(user=user_d.id,acc_type="Long-Term_Debt")

    all = [stt,ltt,std,ltd]
    close_balance = []
    for group in all:
        a = len(group)
        close = 0
        for t in group:
            close += t.close_bal
        close_balance.append(close)

    total = close_balance[0]+close_balance[1]-close_balance[2]-close_balance[3]

    close_balance.append(total)
            

    context = {"stt":stt,"ltt":ltt,"std":std,"ltd":ltd,"close_balance":close_balance}
    return render(request, "ticks_app/accounts/balance.html",context)


def settings(request):
    return render(request, "ticks_app/accounts/settings.html")

def cap_returns(user_d):
    verify = Capacity.objects.filter(user=user_d.id).first()
    if verify is None:
        cap = 0 
    else:
        cap = Capacity.objects.filter(user=user_d.id)
        cap = cap[0]
    return cap

def setup(request):

    user_d = request.user
    cap = cap_returns(user_d)

    if "start_day" in request.POST and "day_button" in request.POST:
        start_day = int(request.POST['start_day'])
        user = User.objects.get(id=user_d.id)

        if (start_day == "" or start_day==" "):
            messages.warning(request,"Entered an empty variable")
        else:
            if start_day > 30:
                messages.warning(request,"Day Entered is greater than 30")
            else:
                
                verify = Capacity.objects.filter(user=user).first()
                if verify is None:
                    Capacity.capInstanceCreate(user,start_day)
                    messages.success(request,"Your Start day has been successfully Updated")
                    cap = cap_returns(user_d)
                    context = {"cap":cap}
                    return render(request, "ticks_app/accounts/settings/setup.html",context)
                else:
                    Capacity.objects.filter(user=user).update(start_date=start_day)
                    messages.success(request,"Your Start day has been successfully Updated")

                    cap = cap_returns(user_d)
                    context = {"cap":cap}
                    return render(request, "ticks_app/accounts/settings/setup.html",context)
                

    elif "saving_button" in request.POST and "savings" in request.POST and "income" in request.POST:
        savings = float(request.POST['savings'])
        income = float(request.POST['income'])
        user = User.objects.get(id=user_d.id)

        if (savings == "" or savings==" " or savings>50000):
            messages.warning(request,"Invalid savings inputs")
        else:
            if (income == "" or savings==" " or income>50000):
                messages.warning(request,"Invalid savings inputs")
            else:
                verify = Capacity.objects.filter(user=user).first()
                if verify is None:
                    messages.warning(request,"Please first create a start day Cap")
                else:
                    Capacity.savingIncomeCap(user,savings,income)
                    messages.success(request,"Incoming and Savings successfully updated")
                    context = {"cap":cap}
                    return render(request, "ticks_app/accounts/settings/setup.html",context)


    
    context = {"cap":cap}
    return render(request, "ticks_app/accounts/settings/setup.html",context)


def financialBehaviour(request):

    user_d = request.user
    verify = Capacity.objects.filter(user=user_d.id).first()
    if verify is None:
        pass
    else:

        fd = Capacity.objects.get(user=user_d.id)
        income = fd.income
        savings = fd.savings
        fd = fd.start_date

        disposable = income-savings

        target = disposable/31

        now = timezone.now()
        obj = [now.year,now.month,now.day]

        if fd > 28 and now.month == 2:
            fd = 28
        else:
            pass
        df = pd.DataFrame()

        #For column Date
        my_date = timezone.datetime(obj[0], obj[1], fd, 0, 0, 0,tzinfo=pytz.timezone('Africa/Johannesburg'))

        if my_date > now:
            month = obj[1] -1
            my_date = timezone.datetime(obj[0], month, fd, 0, 0, 0,tzinfo=pytz.timezone('Africa/Johannesburg'))
        else:
            my_date = timezone.datetime(obj[0], obj[1], fd, 0, 0, 0,tzinfo=pytz.timezone('Africa/Johannesburg'))

        
        date = []
        end_date = my_date + timedelta(days=31)
        date_range = [my_date,end_date]
        n = 1
        for i in range(32):
            date.append(my_date)
            my_date += timedelta(days=n)

        df['DateTime'] = date


        #For column totals
        values = []
        for i in date:
            exclude_items = Q(items = "Income")| Q(items="Inter-AccountTransfer")
            el = Transactions.objects.exclude(exclude_items).filter(trans_date__date=i.date(),user=user_d.id).aggregate(total_amount=Sum('amount'))['total_amount']
            if el is None:
                el = 0
            else:
                pass
            values.append(el)
        
        df['values'] = values

        #For columsn left
        left_dis = []
        for i in values:
            disposable = disposable - i
            left_dis.append(disposable)

        df['left'] = left_dis

        #for target Column 
        target_cap = []
        for i in values:
            target_cap.append(target)

        df['target_cap'] = target_cap

        #for days left
        t_capacity = []


        index = 31
        for i in range(len(left_dis)):
                
                tc = left_dis[i]/index
                t_capacity.append(tc)

                index = index - 1

                if index == 0:
                    index = index +1

        df['t_capacity'] = t_capacity     

        fig = px.line(df, x="DateTime", y="t_capacity", title='Life expectancy in Canada')
        fig.update_layout(title = "Transaction Capacity",
                        yaxis_title = "Rands",
                        xaxis_title = "FinancialM")
        fig.add_hline(y=df['target_cap'][0], line_width=3, line_dash="dash", line_color="blue")
        
        chart = fig.to_html()

        #Items Charst
        exclude_items = Q(items = "Income")| Q(items="Inter-AccountTransfer")
        data = Transactions.objects.exclude(exclude_items).filter(user=user_d.id,trans_date__range=date_range).values("items").annotate(total = Sum('amount'))
        print(len(data))
        if len(data) == 0:
            chart1 = 0
        else:
            fig1 = px.bar(
                x = [c.get('items') for c in data],
                y = [c.get('total') for c in data],
                text = [c.get('total') for c in data], 
            )
            fig1.update_layout(title = "ItemsExpense",
                    yaxis_title = "Amount",
                    xaxis_title = "Items")
            
            chart1 = fig1.to_html





    return render(request,"ticks_app/accounts/behaviour.html",{"chart":chart,"chart1":chart1})

def chartItems():
    pass


def notes(request):
    return render(request, "ticks_app/accounts/settings/notes.html")