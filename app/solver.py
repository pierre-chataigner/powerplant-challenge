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


def get_sum_of_pmax(powerplants,fuels):
	sum=0
	for powerplant in powerplants:
		if powerplant['type'] == 'windturbine':
			sum+=powerplant['pmax']*fuels['wind(%)']/100 
		else:
			sum+=powerplant['pmax']
	return sum


def get_sum_of_pmin(powerplants, fuels):
	sum=0
	for powerplant in powerplants:
		if powerplant['type'] == 'windturbine':
			sum+=powerplant['pmin']*fuels['wind(%)']/100 
		else:
			sum+=powerplant['pmin']
	return sum

def get_minimum_of_pmin(powerplants):
	minimum=float('inf')
	for powerplant in powerplants:
		if powerplant['pmin'] < minimum:
			minimum = powerplant['pmin']
	return minimum


def get_checks(data):
	"""
	:param : "data" is the dictionnary containing the data of the loaded json file that the user upload on the API
	:returns either :
		True, ""                if the data is well defined, without errors
		False, "error message"  if the data contains a error
	"""
	##################### check every value appear (pmin, pmax, co2, load, fuels ...) in the file #####################
	## 'load', 'fuels', 'powerplants'
	for word in ['load', 'fuels', 'powerplants']:
		if word not in data.keys():
			return False, "Variable '{}' not in file or wrongly placed".format(word)
	
	## is fuels a dict ?
	if not type(data['fuels']) is dict:
		return False, "'fuels' is not a dict"
	
	## does fuels have more info than "gas(euro/MWh)","kerosine(euro/MWh)","co2(euro/ton)","wind(%)" ?
	if len(data['fuels']) != 4:
		return False,'"Fuels" must have 4 values : "gas(euro/MWh)","kerosine(euro/MWh)","co2(euro/ton)","wind(%)"'
	
	
	## does all the fuels have their info ?
	for word in ["gas(euro/MWh)","kerosine(euro/MWh)","co2(euro/ton)","wind(%)"]:
		if word not in data['fuels'].keys():
			return False, "Variable '{}' not in fuels".format(word)
	
	## is powerplants a list ?
	if not type(data['powerplants']) is list:
		return False, "'powerplants' is not a list"
	
	## is powerplants empty ?
	if len(data['powerplants']) == 0:
		return False, "'powerplants' is an empty list"

	## does all the powerplant have their variables (pmin,pmax, name, type and efficiency) ?
	for i, powerplant in enumerate(data["powerplants"]):
		if not type(powerplant) is dict:
			return False, "'powerplants' is not a list of dictionnaries"
		for word in ['pmin', 'pmax', 'name', 'type', 'efficiency']:
			if word not in powerplant.keys():
				return False, "Variable '{}' not in the {}th powerplant".format(word,i+1)
	
	
	##################### check the consistency of the values ###########################
	load = data['load']
	fuels = data['fuels']
	powerplants = data['powerplants']
	
	## is load a positive number
	if not type(load) is int and not type(load) is float:
		return False, "'load' must be a number"
	if load <= 0:
		return False, "'load' must be non negative"
	
	##  are fuels values numbers and are they positives
	for fuelname, fuelvalue in fuels.items():
		if not type(fuelvalue) is int and not type(fuelvalue) is float:
			return False, "'{}' must be a number".format(fuelname)
		if fuelvalue < 0:
			return False, "'{}' must be non negative".format(fuelname)
	
	## is wind(%) a number beetween 0 and 100
	if not 0 <= fuels["wind(%)"] <= 100:
		return False, "'wind' must be in percentage (beetween 0 and 100)"
	
	
	## for the powerplants
	for i, powerplant in enumerate(data["powerplants"]):
		# is powerplant name a string ?
		if not type(powerplant["name"]) is str:
			return False, "'name' of the {}th powerplant must be a string".format(i+1)
		# is powerplant type a string ?
		if not type(powerplant["type"]) is str:
			return False, "'type' of the {}th powerplant must be a string".format(i+1)
		# is powerplant type in gasfired, turbojet, windturbine ?
		if not powerplant["type"] in ["gasfired", "turbojet", "windturbine"]:
			return False, '"type" of the {}th powerplant must be in ["gasfired", "turbojet", "windturbine"]'.format(i+1)
		# is efficiency a number beetween 0 and 1 ?
		if not type(powerplant["efficiency"]) is int and not type(powerplant["efficiency"]) is float:
			return False, "'efficiency' must be a number"
		if not 0 <= powerplant["efficiency"] <= 1:
			return False, "'efficiency' must be beetween 0 and 1"
		# is pmin a non negative number ?
		if not type(powerplant["pmin"]) is int and not type(powerplant["pmin"]) is float:
			return False, "'pmin' must be a number"
		if not 0 <= powerplant["pmin"]:
			return False, "'pmin' must superior to 0"
		# is pmax a non negative number ?
		if not type(powerplant["pmax"]) is int and not type(powerplant["pmax"]) is float:
			return False, "'pmax' must be a number"
		if not 0 <= powerplant["pmax"]:
			return False, "'pmax' must superior to 0"
		
		#is load superior to the sum of pmax ?
		if load > get_sum_of_pmax(powerplants, fuels):
			return False, "Sum of 'pmax' ({}) too low compared to 'load' ({})".format(get_sum_of_pmax(powerplants, fuels), load)
		#is load inferior to the lower pmin ?
		if load < get_minimum_of_pmin(powerplants):
			return False, "lower 'pmin' ({}) too high compared to 'load' ({})".format(get_minimum_of_pmin(powerplants), load)
		
	return True, ""

def pprint_powerplants(powerplants):
	r"""
	just a pretty print command for debbuging
	"""
	for powerplant in powerplants:
		print(powerplant)



def solver(powerplants, fuels, load):
	r"""
	:params
		powerplants : any list of dictionary of powerplants THAT ARE ACTIVATED. All of them generate at least a power of pmin
		fuels : the dictionary containing informations on gas, kerosine, co2 and wind
		load : the number the sum of the power of each powerplant must be equal to
	:returns
		solution : vector of p_i. The power each powerplant must generate. The order is the same than the param "powerplant"
		price : how many euros have to be paid with that solution.
	
	
	Let's take an example :
	{
	  "load": 100,
	  "fuels":
	  {
		"gas(euro/MWh)": 13.4,
		"kerosine(euro/MWh)": 50.8,
		"co2(euro/ton)": 20,
		"wind(%)": 60
	  },
	  "powerplants": [
		{
		  "name": "tj1",
		  "type": "turbojet",
		  "efficiency": 0.3,
		  "pmin": 0,
		  "pmax": 16
		},
		{
		  "name": "windpark1",
		  "type": "windturbine",
		  "efficiency": 1,
		  "pmin": 0,
		  "pmax": 150
		},
		{
		  "name": "windpark2",
		  "type": "windturbine",
		  "efficiency": 1,
		  "pmin": 0,
		  "pmax": 150
		}

	  ]
	
	Let's note :
		p_1, p_2 and p_3 :
			the power generated by gasfiredbig1, windpark1 and windpark2 respectively.
		p_min_1 and p_max_1 :
			the pmin and the pmax of gasfiredbig1 (same rule applies for the 2 other powerplant)
		c_i = price_of_resources_by_MWh / efficency_i :
			the price of each powerplant for every MWh they generate
	
	We represent the problem as a minimisation of a linear function with Karush Kuhn and Tucker conditions.
	
	We need to minimize:
	
	J(p) = c_1*p_1 + c_2*p_2 + c_3*p_3 
	
	under the conditions :
	
	p_1 + p_2 + p_3 <= load (can be also written: -load <= -(p_1 + p_2 + p_3))
	p_1 + p_2 + p_3 => load 
	(those two conditions are equivalent to : sum of p_i = load)

	p_min_1 <= p_1
	p_1 <= p_max_1 (can be also written -p_max_2 <= -p_2)
	
	p_min_2 <= p_2
	p_2 <= p_max_2 (can be also written -p_max_2 <= -p_2)
	
	p_min_3 <= p_3
	p_2 <= p_max_3 (can be also written -p_max_2 <= -p_2)
	
	
	The problem can be rewritten as:
	J(p) = <p,c> (dot product)
	
	A_ub @ p <= b_ub (@ is a matricial product)
	where :
	
	A_ub = 
	[[1, 1, 1], 
	 [-1, -1, -1], 
	 [-1, 0, 0], 
	 [1, 0, 0], 
	 [0, -1, 0], 
	 [0, 1, 0], 
	 [0, 0, -1], 
	 [0, 0, 1]]

	b_ub = 
	[100, 
	 -100, 
	 0, 
	 16, 
	 0.0, 
	 90.0, ( = 150*0.60)
	 0.0, 
	 90.0] ( = 150*0.60)

	c = 
	[169.33333333333334, 0, 0]
	because (50.8/0.3 = 169.33333333333334) and wind is free so its cost is zero
	
	
	
	The function will return:
	solution = 
	[ 0. 10. 90.]

	price = 
	0.0

	"""
	
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



def find_best_powers(data):#f is an opened file
	r"""	
	:params
		data : dictionnary data uploaded by user as json
	:returns
		dictionnary that will be send to user and that he/she can store as a json.
		
	We are going to first check the data the user has uploded. Then we are going to solve the problem
	
	As some powerplant can be unactivated we cannot use the classic linear solver with KKT condtions for all powerplants.
	Indeed classic condition is that :
	
	p_i \in [pmin;pmax]
	
	but here, we are in a situation where:
	
	p_i \in [pmin;pmax] \union {0}
	
	because the powerplants can give no power (unactivated) or a power beetween pmin and pmax.
	
	
	To counter that issue we are considering that problem using a brute force algorithm.
	We are testing every combinations of activated powerplant (with checking that they can produce enough enery as their maximum and also not to much as a minimum)
	For each combinations (or each possibility), we are going to pick the one that can :
	-solve all conditions
	-have the lower price (in euros)
	
	That way, we can determine which powerplant must be down (or unactivated) and how much power the other ones have to generate.
	
	"""
	
	checks = get_checks(data)
	if checks[0] == False:
		return checks[1]
	
	
	load = data['load']
	fuels = data['fuels']
	rejected = None # if there is a problem in data, we will save it here

	if DEBUG_DATA:
		debug(load)
		debug(fuels)
		print('powerplant:')
		pprint_powerplants(data['powerplants'])
		print('\n'*6)

	
	all_powerplants = data['powerplants']
	nall_powerplants = len(all_powerplants)

	best_possibility_by_combinations = [] #brute force combinaison to determine every combinations of powerplants
	for j in range(1,nall_powerplants+1):
		for powerplants in it.combinations(all_powerplants, j):
			if DEBUG_BRUTEFORCE:
				print('-----------------------------------------------------------')
			if get_sum_of_pmin(powerplants, fuels) <= load <= get_sum_of_pmax(powerplants, fuels): #reducing computation time
				if DEBUG_BRUTEFORCE:
					print('powerplants:')
					pprint_powerplants(powerplants)
				best_possibility_by_combinations.append([powerplants,*solver(powerplants, fuels, load)])



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
