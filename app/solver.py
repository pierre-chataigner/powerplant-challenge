import numpy as np
import itertools as it
from scipy import optimize
import json
import inspect
import re

def debug(x):
    frame = inspect.currentframe().f_back
    s = inspect.getframeinfo(frame).code_context[0]
    r = re.search(r"\((.*)\)", s).group(1)
    print("{} = \n{}\n".format(r,x))

DEBUG_DATA = False
DEBUG_SOLVER = False
DEBUG_BRUTEFORCE = False
DEBUG_POSSIBILITIES = False

#TODO faire tous les cas (si il n'y a pas de windturbine ou pas de kerosine plant
def find_best_powers(data):#f is an opened file

    def pprint_powerplants(powerplants):
        for powerplant in powerplants:
            print(powerplant)


    load = data['load']
    fuels = data['fuels']
    rejected = None # if there is a problem in data, we will save it here

    if DEBUG_DATA:
        debug(load)
        debug(fuels)
        print('powerplant:')
        pprint_powerplants(data['powerplants'])
        print('\n'*6)

    def check_pmax_all_powerplants(powerplants):
        if load < get_sum_of_pmax(powerplants):
            return True
        else:
            return False


    def get_sum_of_pmin(powerplants):
        sum=0
        for powerplant in powerplants:
            if powerplant['type'] == 'windturbine':
                sum+=powerplant['pmin']*fuels['wind(%)']/100 
            else:
                sum+=powerplant['pmin']
        return sum

    def get_sum_of_pmax(powerplants):
        sum=0
        for powerplant in powerplants:
            if powerplant['type'] == 'windturbine':
                sum+=powerplant['pmax']*fuels['wind(%)']/100 
            else:
                sum+=powerplant['pmax']
        return sum

    def solver(powerplants):

        #cost_gas = fuels['gas(euro/MWh)']
        #cost_kerosine = fuels['kerosine(euro/MWh)']
        #cost_co2 = fuels['co2(euro/ton)']
        #cost_wind = fuels['wind(%)']
        nplants = len(powerplants)

        c = []*nplants
        A_ub = [] # 2 'load' conditions and 2 boundary condition for each powerplant (pmin and pmax)
        b_ub =[]
        bounds=(0, None)



        #load conditions
        # (sum of p_i) <= load
        A_ub.append([1]*nplants)
        b_ub.append(load)

        # load <= (sum of p_i) ( -(sum of p_i) <= -load )
        A_ub.append([-1]*nplants)
        b_ub.append(-load)



        for i, powerplant in enumerate(powerplants): #i is the id of the powerplant
            if powerplant['type'] == 'gasfired':
                c.append(fuels['gas(euro/MWh)']/powerplant['efficiency'])

                pminConstraintA = [0]*nplants
                pminConstraintA[i] = -1
                pminConstraintb =  -powerplant['pmin']

                pmaxConstraintA = [0]*nplants
                pmaxConstraintA[i] = 1
                pmaxConstraintb =  powerplant['pmax']

                A_ub.append(pminConstraintA)
                A_ub.append(pmaxConstraintA)
                b_ub.append(pminConstraintb)
                b_ub.append(pmaxConstraintb)


            if powerplant['type'] == 'windturbine':
                c.append(0) #wind is free.

                pminConstraintA = [0]*nplants
                pminConstraintA[i] = -1
                pminConstraintb =  -powerplant['pmin']*fuels['wind(%)']/100 

                pmaxConstraintA = [0]*nplants
                pmaxConstraintA[i] = 1
                pmaxConstraintb =  powerplant['pmax']*fuels['wind(%)']/100

                A_ub.append(pminConstraintA)
                A_ub.append(pmaxConstraintA)
                b_ub.append(pminConstraintb)
                b_ub.append(pmaxConstraintb)
                #ne pas oublier de mettre faire rentrer le vent dans les boundaries

            if powerplant['type'] == 'turbojet':
                c.append(fuels['kerosine(euro/MWh)']/powerplant['efficiency'])

                pminConstraintA = [0]*nplants
                pminConstraintA[i] = -1
                pminConstraintb =  -powerplant['pmin']

                pmaxConstraintA = [0]*nplants
                pmaxConstraintA[i] = 1
                pmaxConstraintb =  powerplant['pmax']

                A_ub.append(pminConstraintA)
                A_ub.append(pmaxConstraintA)
                b_ub.append(pminConstraintb)
                b_ub.append(pmaxConstraintb)    

        solution = optimize.linprog(c = c,
                                    A_ub = A_ub,
                                    b_ub = b_ub,
                                    bounds = bounds,
                                    method='simplex')['x']
        solution = np.around(solution, decimals = 1)
        price = np.dot(solution,c)

        if DEBUG_SOLVER:
            debug(A_ub)
            debug(b_ub)
            debug(c)
            debug(solution)
            debug(price)

        return solution, price


    if check_pmax_all_powerplants(data['powerplants']):
        all_powerplants = data['powerplants']
        nall_powerplants = len(all_powerplants)

        best_possibility_by_combinations = [] #brute force combinaison to determine every combinations of powerplants
        for j in range(1,nall_powerplants+1):
            for powerplants in it.combinations(all_powerplants, j):
                if DEBUG_BRUTEFORCE:
                    print('-----------------------------------------------------------')
                if get_sum_of_pmin(powerplants) <= load <= get_sum_of_pmax(powerplants): #reducing computation time
                    if DEBUG_BRUTEFORCE:
                        print('powerplants:')
                        pprint_powerplants(powerplants)
                    best_possibility_by_combinations.append([powerplants,*solver(powerplants)])


        
        best_price = float('inf') 
        best_possibility = None
        if DEBUG_POSSIBILITIES:
            print('price :')
        for possibility in best_possibility_by_combinations:
            price = possibility[2]
            if DEBUG_POSSIBILITIES:
                print(price)
            if price <= best_price:
                best_possibility = possibility
                best_price = price
        
        result = []
        for powerplant in data['powerplants']:
            is_power_plant_down = True
            for i, powerplant_chosen in enumerate(best_possibility[0]):
                if powerplant_chosen == powerplant:
                    is_power_plant_down = False
                    p = best_possibility[1][i]
            if is_power_plant_down:
                result.append({'name':powerplant['name'], 'p': 0.0})
            else:
                result.append({'name':powerplant['name'], 'p': p})
                
        return result
    else:
        return ['Problem data : sum of pmax ({}) < load ({})'.format(get_sum_of_pmax(data['powerplants']), load)]
