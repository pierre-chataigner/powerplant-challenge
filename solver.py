############################# CHECKING FUNCTIONS ##########################################
def get_sum_of_pmax(powerplants, fuels):
    sum = 0
    for powerplant in powerplants:
        if powerplant["type"] == "windturbine":
            sum += powerplant["pmax"] * fuels["wind(%)"] / 100
        else:
            sum += powerplant["pmax"]
    return sum


def get_sum_of_pmin(powerplants, fuels):
    sum = 0
    for powerplant in powerplants:
        if powerplant["type"] == "windturbine":
            sum += powerplant["pmin"] * fuels["wind(%)"] / 100
        else:
            sum += powerplant["pmin"]
    return sum


def get_minimum_of_pmin(powerplants):
    minimum = float("inf")
    for powerplant in powerplants:
        if powerplant["pmin"] < minimum:
            minimum = powerplant["pmin"]
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
    for word in ["load", "fuels", "powerplants"]:
        if word not in data.keys():
            return False, "Variable '{}' not in file or wrongly placed".format(word)

    ## is fuels a dict ?
    if not type(data["fuels"]) is dict:
        return False, "'fuels' is not a dict"

    ## does fuels have more info than "gas(euro/MWh)","kerosine(euro/MWh)","co2(euro/ton)","wind(%)" ?
    if len(data["fuels"]) != 4:
        return (
            False,
            '"Fuels" must have 4 values : "gas(euro/MWh)","kerosine(euro/MWh)","co2(euro/ton)","wind(%)"',
        )

    ## does all the fuels have their info ?
    for word in ["gas(euro/MWh)", "kerosine(euro/MWh)", "co2(euro/ton)", "wind(%)"]:
        if word not in data["fuels"].keys():
            return False, "Variable '{}' not in fuels".format(word)

    ## is powerplants a list ?
    if not type(data["powerplants"]) is list:
        return False, "'powerplants' is not a list"

    ## is powerplants empty ?
    if len(data["powerplants"]) == 0:
        return False, "'powerplants' is an empty list"

    ## does all the powerplant have their variables (pmin,pmax, name, type and efficiency) ?
    for i, powerplant in enumerate(data["powerplants"]):
        if not type(powerplant) is dict:
            return False, "'powerplants' is not a list of dictionnaries"
        for word in ["pmin", "pmax", "name", "type", "efficiency"]:
            if word not in powerplant.keys():
                return False, "Variable '{}' not in the {}th powerplant".format(
                    word, i + 1
                )

    ##################### check the consistency of the values ###########################
    load = data["load"]
    fuels = data["fuels"]
    powerplants = data["powerplants"]

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
            return False, "'name' of the {}th powerplant must be a string".format(i + 1)
        # is powerplant type a string ?
        if not type(powerplant["type"]) is str:
            return False, "'type' of the {}th powerplant must be a string".format(i + 1)
        # is powerplant type in gasfired, turbojet, windturbine ?
        if not powerplant["type"] in ["gasfired", "turbojet", "windturbine"]:
            return (
                False,
                '"type" of the {}th powerplant must be in ["gasfired", "turbojet", "windturbine"]'.format(
                    i + 1
                ),
            )
        # is efficiency a number beetween 0 and 1 ?
        if (
            not type(powerplant["efficiency"]) is int
            and not type(powerplant["efficiency"]) is float
        ):
            return False, "'efficiency' must be a number"
        if not 0 <= powerplant["efficiency"] <= 1:
            return False, "'efficiency' must be beetween 0 and 1"
        # is pmin a non negative number ?
        if (
            not type(powerplant["pmin"]) is int
            and not type(powerplant["pmin"]) is float
        ):
            return False, "'pmin' must be a number"
        if not 0 <= powerplant["pmin"]:
            return False, "'pmin' must superior to 0"
        # is pmax a non negative number ?
        if (
            not type(powerplant["pmax"]) is int
            and not type(powerplant["pmax"]) is float
        ):
            return False, "'pmax' must be a number"
        if not 0 <= powerplant["pmax"]:
            return False, "'pmax' must superior to 0"

        # is load superior to the sum of pmax ?
        if load > get_sum_of_pmax(powerplants, fuels):
            return False, "Sum of 'pmax' ({}) too low compared to 'load' ({})".format(
                get_sum_of_pmax(powerplants, fuels), load
            )
        # is load inferior to the lower pmin ?
        if load < get_minimum_of_pmin(powerplants):
            return False, "lower 'pmin' ({}) too high compared to 'load' ({})".format(
                get_minimum_of_pmin(powerplants), load
            )

    return True, ""


############################# SOLVER FUNCTIONS ##########################################


def preprocessing(load, fuels, powerplants):
    # Add cost to powerplants
    for powerplant in powerplants:
        powerplant["cost"] = (
            (powerplant["type"] == "windturbine") * 0
            + (powerplant["type"] == "gasfired") * fuels["gas(euro/MWh)"]
            + (powerplant["type"] == "turbojet") * fuels["kerosine(euro/MWh)"]
        )

    # Reduce windturbines pmin and pmax because of wind
    for powerplant in powerplants:
        if powerplant["type"] == "windturbine":
            powerplant["pmax"] = powerplant["pmax"] * fuels["wind(%)"] / 100
    return load, fuels, powerplants


def postprocessing(production_plan):
    for powerplant in production_plan:
        powerplant["p"] = round(float(powerplant["p"]), 1)
    return production_plan


def calculate_production_plan(load, fuels, powerplants):
    # Sort powerplants based on cost, efficiency, pmin and pmax
    sorted_powerplants = sorted(
        powerplants, key=lambda p: (p["cost"], p["efficiency"], p["pmin"], -p["pmax"])
    )

    # Initialize variables
    remaining_load = load
    production_plan = []

    # Iterate over powerplants and allocate power based on merit-order
    for powerplant in sorted_powerplants:
        pmax = powerplant["pmax"]
        pmin = powerplant["pmin"]

        # Calculate the maximum power that can be allocated for the powerplant
        max_power = min(remaining_load, pmax)

        # Calculate the power to be allocated while considering pmin
        allocated_power = max(max_power, pmin)

        # Update the remaining load and power production plan
        remaining_load -= allocated_power
        production_plan.append({"name": powerplant["name"], "p": allocated_power})

        # Keep the last powerplant in a variable for later
        last_powerplant = powerplant

        # Break the loop if the remaining load is lower or equal to 0
        if remaining_load <= 0:
            break

    if remaining_load == 0:
        return production_plan

    else:  # when remaining_load > 0 because the pmin of the last powerplant is too high
        first_powerplants = powerplants.copy()
        first_powerplants.remove(last_powerplant)
        load4first_powerplants = load - last_powerplant["pmin"]

        # we re-calculate the production plan but we force the last powerplant to be added with its pmin as power
        return [
            {"name": last_powerplant["name"], "p": last_powerplant["pmin"]}
        ] + calculate_production_plan(
            powerplants=first_powerplants, load=load4first_powerplants, fuels=fuels
        )
