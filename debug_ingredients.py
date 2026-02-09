import xml.etree.ElementTree as ET

# Parse a sample recipe
input_file = "Input/Rifle/127x55mm.xml"
tree = ET.parse(input_file)
root = tree.getroot()

# Find Incendiary recipe
for recipe in root.findall('.//RecipeDef'):
    def_name = recipe.find('defName')
    if def_name is not None and def_name.text == "MakeAmmo_127x55mm_Incendiary":
        print(f"Found recipe: {def_name.text}")
        
        # Get ingredients
        ingredients = recipe.find('ingredients')
        if ingredients is not None:
            ingredient_elements = ingredients.findall('li')
            print(f"Found {len(ingredient_elements)} ingredient elements")
            
            for i, ing in enumerate(ingredient_elements):
                mat = ing.find('.//li')
                count = ing.find('count')
                print(f"  {i}: Material={mat.text if mat is not None else 'None'}, Count={count.text if count is not None else 'None'}")
            
            # Try to remove them
            total_cost = 0
            for ingredient in ingredient_elements:
                count_elem = ingredient.find('count')
                if count_elem is not None:
                    try:
                        total_cost += int(count_elem.text)
                    except (ValueError, TypeError):
                        pass
            print(f"Total cost: {total_cost}")
            
            # Make a copy and test removal
            recipe_copy = ET.fromstring(ET.tostring(recipe))
            ingredients_copy = recipe_copy.find('ingredients')
            ingredient_elements_copy = ingredients_copy.findall('li')
            print(f"Copy has {len(ingredient_elements_copy)} ingredients")
            
            for ing in ingredient_elements_copy:
                ingredients_copy.remove(ing)
            print(f"After removal: {len(ingredients_copy.findall('li'))} ingredients")
            
            # Add new ones
            for i, material in enumerate(["Bioferrite", "Uranium", "Steel"]):
                new_ingredient = ET.Element('li')
                filter_elem = ET.SubElement(new_ingredient, 'filter')
                thing_defs = ET.SubElement(filter_elem, 'thingDefs')
                li_def = ET.SubElement(thing_defs, 'li')
                li_def.text = material
                count_elem = ET.SubElement(new_ingredient, 'count')
                count_elem.text = str(100 + i)
                ingredients_copy.append(new_ingredient)
            
            print(f"After adding: {len(ingredients_copy.findall('li'))} ingredients")
            for ing in ingredients_copy.findall('li'):
                mat = ing.find('.//li')
                count = ing.find('count')
                print(f"  Material={mat.text if mat is not None else 'None'}, Count={count.text if count is not None else 'None'}")
        
        break
