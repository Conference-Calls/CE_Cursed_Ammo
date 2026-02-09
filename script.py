import xmltodict
import os

def try_deepset_attr(obj, key, value):
    if not isinstance(obj, (dict, list)):
        return
    if isinstance(obj, dict):
        if key in obj.keys() and isinstance(obj[key], str):
            obj[key] = value
        for v in obj.values():
            try_deepset_attr(v, key, value)
    elif isinstance(obj, list):
        for item in obj:
            try_deepset_attr(item, key, value)

def try_deeprm_attr(obj, key):
    if not isinstance(obj, (dict, list)):
        return
    if isinstance(obj, dict):
        if key in obj.keys():
            del obj[key]
        for v in obj.values():
            try_deeprm_attr(v, key)
    elif isinstance(obj, list):
        for item in obj:
            try_deeprm_attr(item, key)

def try_deeprm_attr_with_property(obj, property):
    if not isinstance(obj, (dict, list)):
        return
    if isinstance(obj, dict):
        if "ThingDef" in obj.keys() and property in obj["ThingDef"][0].keys():
            del obj["ThingDef"]
        for v in obj.values():
            try_deeprm_attr_with_property(v, property)
    elif isinstance(obj, list):
        for item in obj:
            try_deeprm_attr_with_property(item, property)

def main():
    for root, dirs, files in os.walk("."):
        for file in files:
            if file.endswith(".xml"):
                try:
                    with open(os.path.join(root, file), "r") as f:
                        data = xmltodict.parse(f.read())
                        try_deeprm_attr_with_property(data, "@Abstract")
                    with open(os.path.join(root, file), "w") as f:
                        f.write(xmltodict.unparse(data, pretty=True))
                except Exception as e:
                    print(f"Failed to process {file}: {e}")

if __name__ == "__main__":
    main()
        