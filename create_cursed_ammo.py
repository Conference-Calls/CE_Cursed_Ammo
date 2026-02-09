import xml.etree.ElementTree as ET
import os
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import xmltodict

# Configuration for variant creation
VARIANT_CONFIGS = {
    "EAC_Bioferrite": {
        "base_ammo_class": "IncendiaryAP",  # Based on AP-I (IncendiaryAP)
        "sharp_penetration_modifier": 1.5,  # Increase by 50%
        "damage_modifier": 0.8,  # Reduce by 20%
        "recipe_materials": {
            "Bioferrite": 0.4,
            "Uranium": 0.4,
            "Steel": 0.2
        },
        "label": "bioferrite penetrator",
        "label_short": "Bioferrite",
        "texture_suffix": "EAC_Bioferrite",
        "damage_type": "Bullet"  # Remain as Bullet damage
    },
    "EAC_Silver": {
        "base_ammo_class": "ArmorPiercing",  # Based on AP
        "sharp_penetration_modifier": 999999,  # Set to 999999
        "damage_modifier": 2.0,  # Double damage
        "recipe_materials": {
            "Silver": 1.0,
            "Shard": 1.0  # 1 Shard added
        },
        "label": "consecrated silver",
        "label_short": "Consecrated",
        "texture_suffix": "EAC_Silver",
        "damage_type": "Disintegrate"  # Change to Disintegrate
    }
}


def get_ammo_set_info(root: ET.Element, ammo_type: str) -> Optional[Tuple[str, str]]:
    """Extract internal ammo naming and AmmoSet defName from the input XML.
    
    Returns: (internal_ammo_name, ammo_set_def_name) or None if not found
    """
    # Find the AmmoSetDef to extract both the internal naming and the set name
    for ammo_set in root.findall('.//CombatExtended.AmmoSetDef'):
        ammo_set_name = ammo_set.find('defName')
        if ammo_set_name is None or not ammo_set_name.text:
            continue
        
        # The AmmoSetDef name typically follows the pattern AmmoSet_<internal_name>
        # e.g., AmmoSet_65x48mmCreedmoor
        ammo_set_def = ammo_set_name.text
        if ammo_set_def.startswith('AmmoSet_'):
            internal_ammo_name = ammo_set_def.replace('AmmoSet_', '')
            return internal_ammo_name, ammo_set_def
    
    return None


def get_ammo_caliber_name(filename: str) -> str:
    """Extract caliber name from filename (remove .xml extension)."""
    return filename.replace('.xml', '')


def find_ap_ammo_def(root: ET.Element, ammo_type: str, base_ammo_class: str) -> Optional[ET.Element]:
    """Find AP or AP-I ammo definition in the XML based on base_ammo_class."""
    # First try exact match with filename-based ammo_type
    for ammo_def in root.findall('.//ThingDef[@Class="CombatExtended.AmmoDef"]'):
        def_name = ammo_def.find('defName')
        ammo_class_elem = ammo_def.find('ammoClass')
        if (def_name is not None and def_name.text and 
            def_name.text.startswith(f"Ammo_{ammo_type}_") and
            ammo_class_elem is not None and ammo_class_elem.text == base_ammo_class):
            return ammo_def
    
    # If no exact match, just find any ammo with the matching base_ammo_class
    # This handles cases where internal naming differs from filename
    for ammo_def in root.findall('.//ThingDef[@Class="CombatExtended.AmmoDef"]'):
        def_name = ammo_def.find('defName')
        ammo_class_elem = ammo_def.find('ammoClass')
        if (def_name is not None and def_name.text and 
            def_name.text.startswith("Ammo_") and
            ammo_class_elem is not None and ammo_class_elem.text == base_ammo_class):
            return ammo_def
    
    return None


def find_ap_bullet_def(root: ET.Element, def_name: str) -> Optional[ET.Element]:
    """Find bullet projectile definition by linked ammo name."""
    for bullet_def in root.findall('.//ThingDef[@ParentName]'):
        bullet_name = bullet_def.find('defName')
        if bullet_name is not None and bullet_name.text:
            # Match bullet name to ammo name (Ammo_X_Y -> Bullet_X_Y)
            expected_bullet_name = def_name.replace("Ammo_", "Bullet_")
            if bullet_name.text == expected_bullet_name and bullet_def.find('projectile') is not None:
                return bullet_def
    return None


def find_ap_recipe(root: ET.Element, def_name: str) -> Optional[ET.Element]:
    """Find recipe definition by linked ammo name."""
    expected_recipe_name = def_name.replace("Ammo_", "MakeAmmo_")
    for recipe in root.findall('.//RecipeDef'):
        recipe_name = recipe.find('defName')
        if recipe_name is not None and recipe_name.text == expected_recipe_name:
            return recipe
    return None


def deep_copy_element(element: ET.Element) -> ET.Element:
    """Create a deep copy of an XML element."""
    return ET.fromstring(ET.tostring(element))


def create_cursed_ammo_variant(
    root: ET.Element,
    ammo_type: str,
    variant_key: str,
    config: Dict
) -> Tuple[Optional[ET.Element], Optional[ET.Element], Optional[ET.Element]]:
    """Create cursed ammo variants (ammo def, bullet def, recipe) from AP types."""
    
    # Find the base AP definitions using the configured base_ammo_class
    base_ammo_class = config['base_ammo_class']
    ap_ammo = find_ap_ammo_def(root, ammo_type, base_ammo_class)
    
    if ap_ammo is None:
        return None, None, None
    
    # Debug: print what we found
    ammo_def_name = ap_ammo.find('defName').text
    ap_bullet = find_ap_bullet_def(root, ammo_def_name)
    ap_recipe = find_ap_recipe(root, ammo_def_name)
    
    if not (ap_ammo is not None and ap_bullet is not None and ap_recipe is not None):
        return None, None, None
    
    # Create cursed ammo definition
    cursed_ammo = deep_copy_element(ap_ammo)
    def_name_elem = cursed_ammo.find('defName')
    if def_name_elem is not None:
        old_name = def_name_elem.text
        # Replace the variant type (AP, Incendiary, etc) with CursedVariant
        # Find where the variant identifier starts (after the last underscore before the variant)
        parts = old_name.split('_')
        base = '_'.join(parts[:-1])  # Everything except the last part
        new_name = f"{base}_{variant_key}"
        def_name_elem.text = new_name
    
    label_elem = cursed_ammo.find('label')
    if label_elem is not None:
        label_elem.text = f"{ammo_type} ({config['label_short']})"
    
    # Update ammoClass to the variant key
    ammo_class_elem = cursed_ammo.find('ammoClass')
    if ammo_class_elem is not None:
        ammo_class_elem.text = variant_key
    
    # Update cookOffProjectile to point to the cursed bullet
    cookoff_elem = cursed_ammo.find('cookOffProjectile')
    if cookoff_elem is not None:
        cursed_bullet_name = ap_bullet.find('defName').text
        parts = cursed_bullet_name.split('_')
        base = '_'.join(parts[:-1])
        new_bullet_name = f"{base}_{variant_key}"
        cookoff_elem.text = new_bullet_name
    
    # Update texture path
    graphic_elem = cursed_ammo.find('.//graphicData/texPath')
    if graphic_elem is not None:
        # Replace the texture path to use the variant suffix
        if graphic_elem.text:
            # Replace the last part with the new suffix
            parts = graphic_elem.text.split('/')
            parts[-1] = config['texture_suffix']
            graphic_elem.text = '/'.join(parts)
    
    # Create cursed bullet definition
    cursed_bullet = deep_copy_element(ap_bullet)
    def_name_elem = cursed_bullet.find('defName')
    if def_name_elem is not None:
        old_name = def_name_elem.text
        # Replace the variant type in bullet name (e.g., Bullet_X_AP -> Bullet_X_Variant)
        parts = old_name.split('_')
        base = '_'.join(parts[:-1])  # Everything except the last part
        new_name = f"{base}_{variant_key}"
        def_name_elem.text = new_name
    
    label_elem = cursed_bullet.find('label')
    if label_elem is not None:
        # Replace (AP), (AP-I), or any similar parenthetical with the new label
        label_elem.text = re.sub(r'\([^)]*\)', f'({config["label_short"]})', label_elem.text)
    
    # Update bullet projectile properties
    projectile = cursed_bullet.find('projectile')
    if projectile is not None:
        # Update sharp penetration
        penetration_elem = projectile.find('armorPenetrationSharp')
        if penetration_elem is not None:
            try:
                old_value = float(penetration_elem.text)
                # For Silver variant, set to 999999 directly; for others, multiply
                if config['sharp_penetration_modifier'] >= 1000:  # Silver variant
                    new_value = config['sharp_penetration_modifier']
                else:
                    new_value = old_value * config['sharp_penetration_modifier']
                    new_value = round(new_value)
                penetration_elem.text = str(int(new_value))
            except (ValueError, TypeError):
                pass
        
        # Update damage
        damage_elem = projectile.find('damageAmountBase')
        if damage_elem is not None:
            try:
                old_value = float(damage_elem.text)
                new_value = old_value * config['damage_modifier']
                new_value = round(new_value)
                damage_elem.text = str(int(new_value))
            except (ValueError, TypeError):
                pass
        
        # Update damage type if needed
        damage_def_elem = projectile.find('damageDef')
        if damage_def_elem is not None and config['damage_type'] != "Bullet":
            damage_def_elem.text = config['damage_type']
        
        # For EAC_Silver: remove secondary damage and ensure primary damage is Disintegrate
        if variant_key == "Silver":
            secondary_damage = projectile.find('secondaryDamage')
            if secondary_damage is not None:
                projectile.remove(secondary_damage)
    
    # Create cursed recipe definition
    cursed_recipe = deep_copy_element(ap_recipe)
    def_name_elem = cursed_recipe.find('defName')
    if def_name_elem is not None:
        old_name = def_name_elem.text
        # Replace the variant type in recipe name
        parts = old_name.split('_')
        base = '_'.join(parts[:-1])  # Everything except the last part
        new_name = f"{base}_{variant_key}"
        def_name_elem.text = new_name
    
    label_elem = cursed_recipe.find('label')
    if label_elem is not None:
        # Replace (AP), (AP-I), or any similar parenthetical with the new label
        label_elem.text = re.sub(r'\([^)]*\)', f'({config["label_short"]})', label_elem.text)
    
    # Update description and jobString
    description_elem = cursed_recipe.find('description')
    if description_elem is not None:
        description_elem.text = re.sub(r'\([^)]*\)', f'({config["label_short"]})', description_elem.text)
    
    jobstring_elem = cursed_recipe.find('jobString')
    if jobstring_elem is not None:
        jobstring_elem.text = re.sub(r'\([^)]*\)', f'({config["label_short"]})', jobstring_elem.text)
    
    # Update recipe ingredients
    ingredients = cursed_recipe.find('ingredients')
    if ingredients is not None:
        # Get the original ingredient count to calculate proportions
        ingredient_elements = ingredients.findall('li')
        
        # Extract the first ingredient count for use in Silver variant
        first_ingredient_count = "82"  # Default fallback
        if ingredient_elements and ingredient_elements[0].find('count') is not None:
            try:
                first_ingredient_count = ingredient_elements[0].find('count').text
            except (AttributeError, ValueError, TypeError):
                pass
        
        if variant_key == "EAC_Bioferrite":
            # Find the first ingredient's count (typically Steel)
            total_cost = 0
            for ingredient in ingredient_elements:
                count_elem = ingredient.find('count')
                if count_elem is not None:
                    try:
                        total_cost += int(count_elem.text)
                    except (ValueError, TypeError):
                        pass
            
            # Remove all existing ingredients
            for ing in list(ingredient_elements):
                ingredients.remove(ing)
            
            # Add new ingredients with calculated amounts
            materials_in_order = ["Bioferrite", "Uranium", "Steel"]
            for material in materials_in_order:
                proportion = config['recipe_materials'][material]
                count = int(round(total_cost * proportion))
                
                new_ingredient = ET.Element('li')
                filter_elem = ET.SubElement(new_ingredient, 'filter')
                thing_defs = ET.SubElement(filter_elem, 'thingDefs')
                li_def = ET.SubElement(thing_defs, 'li')
                li_def.text = material
                
                count_elem = ET.SubElement(new_ingredient, 'count')
                count_elem.text = str(count)
                
                ingredients.append(new_ingredient)
        
        elif variant_key == "EAC_Silver":
            # Replace with Silver + 1 Shard
            ingredient_list = list(ingredients.findall('li'))
            for ing in ingredient_list:
                ingredients.remove(ing)
            
            # Add Silver
            silver_ingredient = ET.Element('li')
            filter_elem = ET.SubElement(silver_ingredient, 'filter')
            thing_defs = ET.SubElement(filter_elem, 'thingDefs')
            li_def = ET.SubElement(thing_defs, 'li')
            li_def.text = "Silver"
            count_elem = ET.SubElement(silver_ingredient, 'count')
            count_elem.text = first_ingredient_count
            ingredients.append(silver_ingredient)
            
            # Add Shard
            shard_ingredient = ET.Element('li')
            filter_elem = ET.SubElement(shard_ingredient, 'filter')
            thing_defs = ET.SubElement(filter_elem, 'thingDefs')
            li_def = ET.SubElement(thing_defs, 'li')
            li_def.text = "Shard"
            count_elem = ET.SubElement(shard_ingredient, 'count')
            count_elem.text = "1"
            ingredients.append(shard_ingredient)
    
    # Update fixedIngredientFilter
    fixed_filter = cursed_recipe.find('fixedIngredientFilter')
    if fixed_filter is not None:
        thing_defs = fixed_filter.find('thingDefs')
        if thing_defs is not None:
            # Clear existing
            for li in thing_defs.findall('li'):
                thing_defs.remove(li)
            
            # Add new materials
            if variant_key == "EAC_Bioferrite":
                materials = ["Bioferrite", "Uranium", "Steel"]
            else:  # EAC_Silver
                materials = ["Silver", "Shard"]
            
            for material in materials:
                li_elem = ET.SubElement(thing_defs, 'li')
                li_elem.text = material
    
    # Update product reference in recipe
    products = cursed_recipe.find('products')
    if products is not None:
        # Get the new ammo name we created
        new_ammo_name = cursed_ammo.find('defName').text
        
        # Find and update the product element
        for product_elem in list(products):
            if product_elem.tag.startswith("Ammo_"):
                # Store the count
                count_text = product_elem.text
                # Remove old element
                products.remove(product_elem)
                # Add new element with the cursed ammo name
                new_product = ET.SubElement(products, new_ammo_name)
                new_product.text = count_text
                break
    
    return cursed_ammo, cursed_bullet, cursed_recipe


def process_input_file(input_path: str, output_dir: str) -> Optional[Tuple[str, str]]:
    """Process a single input XML file and create cursed variants.
    
    Returns: (internal_ammo_name, ammo_set_def_name) or None if failed
    """
    
    try:
        # Read file content and remove BOM/leading bytes for clean XML parsing
        with open(input_path, 'r', encoding='utf-8-sig') as file:
            content = file.read()
        
        # Remove any Unicode BOM characters that might still be present
        content = content.lstrip('\ufeff')
        
        # Parse the cleaned XML content
        root = ET.fromstring(content)
        
        # Get caliber name from filename
        filename = os.path.basename(input_path)
        ammo_type = get_ammo_caliber_name(filename)
        
        # Get ammo set information for patch generation
        ammo_set_info = get_ammo_set_info(root, ammo_type)
        
        # Create output document with only cursed variants
        output_root = ET.Element('Defs')
        
        # Try to create each variant
        for variant_key, config in VARIANT_CONFIGS.items():
            cursed_ammo, cursed_bullet, cursed_recipe = create_cursed_ammo_variant(
                root, ammo_type, variant_key, config
            )
            
            if cursed_ammo is not None:
                output_root.append(cursed_ammo)
            if cursed_bullet is not None:
                output_root.append(cursed_bullet)
            if cursed_recipe is not None:
                output_root.append(cursed_recipe)
        
        # Write output file to the appropriate subdirectory
        output_path = os.path.join(output_dir, filename)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        indent_tree(output_root)
        tree = ET.ElementTree(output_root)
        tree.write(output_path, encoding='utf-8', xml_declaration=True)
        
        print(f"[OK] Processed: {filename}")
        
        # Return ammo set info for patch file generation
        return ammo_set_info
        
    except ET.ParseError as e:
        print(f"[ERROR] XML parsing failed for {input_path}: {e}")
    except Exception as e:
        print(f"[ERROR] Failed to process {input_path}: {e}")
    
    return None


def generate_patch_file(ammo_set_infos: List[Tuple[str, str]], output_base_dir: Path) -> None:
    """Generate a patch file to add cursed ammo types to their AmmoSets.
    
    Args:
        ammo_set_infos: List of (internal_ammo_name, ammo_set_def_name) tuples
        output_base_dir: Path to output directory
    """
    if not ammo_set_infos:
        print("[WARNING] No ammo set information collected, skipping patch file generation")
        return
    
    # Create root patch element
    patch_root = ET.Element('Patch')
    
    # For each ammo type, create operations to add its cursed variants
    for internal_ammo_name, ammo_set_def_name in sorted(ammo_set_infos):
        # Create operation for this ammo set
        operation = ET.Element('Operation')
        operation.set('Class', 'PatchOperationAdd')
        
        # Set xpath to the ammoTypes element
        xpath_elem = ET.Element('xpath')
        xpath_elem.text = f'Defs/CombatExtended.AmmoSetDef[defName="{ammo_set_def_name}"]/ammoTypes'
        operation.append(xpath_elem)
        
        # Create value element with the new ammo entries
        value_elem = ET.Element('value')
        
        # Add EAC_Bioferrite variant
        bioferrite_ammo = f"Ammo_{internal_ammo_name}_EAC_Bioferrite"
        bioferrite_bullet = f"Bullet_{internal_ammo_name}_EAC_Bioferrite"
        bioferrite_entry = ET.Element(bioferrite_ammo)
        bioferrite_entry.text = bioferrite_bullet
        value_elem.append(bioferrite_entry)
        
        # Add EAC_Silver variant
        silver_ammo = f"Ammo_{internal_ammo_name}_EAC_Silver"
        silver_bullet = f"Bullet_{internal_ammo_name}_EAC_Silver"
        silver_entry = ET.Element(silver_ammo)
        silver_entry.text = silver_bullet
        value_elem.append(silver_entry)
        
        operation.append(value_elem)
        patch_root.append(operation)
    
    # Write patch file
    patch_path = output_base_dir / 'AmmoSetAdd_EAC_Cursed.xml'
    indent_tree(patch_root)
    patch_tree = ET.ElementTree(patch_root)
    patch_tree.write(str(patch_path), encoding='utf-8', xml_declaration=True)
    
    print(f"[OK] Generated patch file: {patch_path}")


def indent_tree(elem, level=0):
    """Add pretty-printing indentation to XML tree."""
    indent = "\n" + level * "\t"
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = indent + "\t"
        if not elem.tail or not elem.tail.strip():
            elem.tail = indent
        for child in elem:
            indent_tree(child, level + 1)
        if not child.tail or not child.tail.strip():
            child.tail = indent
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = indent


def main():
    """Main function to process all input files."""
    
    workspace_root = Path(__file__).parent
    input_base_dir = workspace_root / "Input"
    output_base_dir = workspace_root / "Output"
    
    # Create output directory if it doesn't exist
    output_base_dir.mkdir(parents=True, exist_ok=True)
    
    if not input_base_dir.exists():
        print(f"Error: Input directory not found: {input_base_dir}")
        return
    
    print(f"Processing ammo files from: {input_base_dir}")
    print(f"Output directory: {output_base_dir}")
    print()
    
    # Process all XML files recursively in the Input directory and its subfolders
    xml_files = sorted(input_base_dir.glob("**/*.xml"))
    
    if not xml_files:
        print("No XML files found in input directory.")
        return
    
    print(f"Found {len(xml_files)} ammo files to process\n")
    
    # Collect ammo set information for patch file generation
    ammo_set_infos = []
    
    for input_file in xml_files:
        # Get the relative path from Input directory
        relative_path = input_file.relative_to(input_base_dir)
        # Create corresponding output subdirectory
        output_subdir = output_base_dir / relative_path.parent
        
        # Process file and collect ammo set info
        ammo_set_info = process_input_file(str(input_file), str(output_subdir))
        if ammo_set_info:
            ammo_set_infos.append(ammo_set_info)
    
    # Generate patch file with all collected ammo set information
    generate_patch_file(ammo_set_infos, output_base_dir)
    
    print(f"\n[OK] Processing complete! Generated files in: {output_base_dir}")


if __name__ == "__main__":
    main()
