from django.http import HttpResponse
from django.shortcuts import render
from calc.settings import PRODUCT_GROUPS, DEFAULT_PARAMS, API_KEY, API_URL, DEFAULT_ARPU

import requests

STARTING_COST = 15000

def get_arpu_from_marketplace(product_name) -> int:
    try:
        url = f"https://{API_URL}/search?query={product_name}"
        headers = {
            "X-RapidAPI-Host": API_URL,
            "X-RapidAPI-Key": API_KEY,
            "x-rapidapi-ua": "RapidAPI-Playground"
        }

        response = requests.get(url, headers=headers, timeout=100)
        data = response.json()
        products = data['data']['products']
        sum = 0
        count = len(products)
        i = 0
        while i < count:
            product = products[i]
            if product['product_price'] is not None:
                price = float(product['product_price'].replace('$', ''))
                sum += price
            i += 1

        return round(sum / count) if count != 0 else 0
    except Exception as e:
        raise e
        return DEFAULT_ARPU[product_name]

def index(request):
    
    args = DEFAULT_PARAMS

    if 'start_users_count' in request.GET:
        group_product = request.GET['group'].split('-')
        args = {
            'product_name': request.GET['product_name'],
            'group': group_product[0],
            'product': group_product[1],
            'start_users_count': request.GET['start_users_count'],
            'churn_rate': request.GET['churn_rate'],
            'ARPU': request.GET['ARPU'],
            'TCPC': request.GET['TCPC'],
            'target_users_count': request.GET['target_users_count'],
            'discount_rate': request.GET['discount_rate']
        }
        
    results = __calculate_results(args)

    return render(request, 'index.html', {"results": results,
                                          "args": args,
                                          "PRODUCT_GROUPS": PRODUCT_GROUPS})
    
def get_arpu(self, product_name) -> int:
    return HttpResponse(get_arpu_from_marketplace(product_name))

def __calculate_results(args) -> dict:

    initial_customers_number = int(args['start_users_count'])

    if 'market_share' in args:
        market_share = float(args['market_share']) / 100
        customers_share = float(args['customers_share']) / 100
        population = int(args['population'])
        target_customers_number = population * customers_share
    else:
        target_customers_number = int(args['target_users_count'])

    CAGR = (target_customers_number / initial_customers_number) ** (1/5) - 1    

    churn_rate = float(args['churn_rate']) / 100

    ARPU = float(args['ARPU'])
    TCPC = float(args['TCPC'])

    discount_rate = float(args['discount_rate']) / 100
    growth_rate = CAGR * (1 - churn_rate)

    company_value = 0

    result = {
        'users': [initial_customers_number],
        'profit': [0],
        'revenues': [0]
    }

    # year 1
    revenue = ARPU * initial_customers_number * (1 + growth_rate)
    result['revenues'].append(revenue)
    TCPC_per_year = TCPC * (1 + CAGR) * initial_customers_number

    customers = initial_customers_number * (1 + CAGR) * (1 - churn_rate)
    result['users'].append(customers)

    result['profit'].append(revenue - TCPC_per_year)

    if 'market_share' in args:
        market_size = ARPU * population * customers_share * market_share
    else:
        market_size = ARPU * target_customers_number

    result['market_size'] = market_size

    for year in range(2, 6):

        revenue *= (1 + growth_rate)
        result['revenues'].append(revenue)
        
        customers = round(customers * (1 + CAGR) * (1 - churn_rate))
        result['users'].append(customers)

        TCPC_per_year *= (1 + CAGR)
        
        net_profit = revenue - TCPC_per_year

        result['profit'].append(net_profit)

        discount_factor_per_year = 1 / ((1 + discount_rate)**year)
        DCF_per_year = net_profit * discount_factor_per_year
        company_value += DCF_per_year

    result['company_value'] = company_value

    return result