import json, os

enums_path = "/Users/wpotter/Documents/GitHub/sinai_metadata/data-model/jsonschemas/enums.json"
with open(enums_path) as f:
        # read the contents as JSON
        enums = json.load(f)
        defs = enums["$defs"]
        for term_list in defs:
            # only update term lists that are using anyOf
            if "anyOf" in defs[term_list]:
                # print(term_list)
                cv_list = []
                for term in defs[term_list]["anyOf"]:
                     cv_list.append(term["const"])
                # print(cv_list)
                defs[term_list]["enum"] = cv_list
                del(defs[term_list]["anyOf"])
        # currently dumps to console; update to write back to the same file
        print(json.dumps(enums, indent=2))