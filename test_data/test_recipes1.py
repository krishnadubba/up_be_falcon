import json

a={"name": "Beetroot pancakes", 
 "description":"Whizz beetroot into an easy batter to make these bright purple pancakes, then top with a warm fruit compote for a hearty weekend brunch. You can use this recipe to make blini-style canapés, too.",
 "author":"Mirian Nice",
 "steps":["Put the beetroot in a jug with the milk and blend with a stick blender until smooth. Pour into a bowl with the rest of the pancake ingredients and whisk until smooth and vibrant purple.",
        "Put a small knob of butter in a large non-stick frying pan and heat over a medium-low heat until melted and foamy. Now create 3 or 4 pancakes each made from 2 tbsp of the batter. Cook for 2-3 mins then flip over and cook for a further minute until cooked through. Repeat with any remaining batter. Heat oven to lowest setting and keep the pancakes warm in there until needed.",
        "Serve with your favourite pancake toppings or make a simple compote by simmering frozen berries in with 1 tbsp blackcurrant jam until bubbling and syrupy (about 5-10 mins). In a small bowl stir together the remaining jam and the yogurt. Stack the cooked pancakes with the yogurt and pour the warm berry compote over the top."],
 "ingredients":["small cooked whole beetroot chopped",
                "milk", "self raising flour", "baking powder", "maple syrup",
                "vanilla extract", "eggs", "butter, melted plus extra for frying",
                "frozen mixed berries", "blackcurrant jam", "Greek yogurt"],
 "ingredients_quant":[3, 50, 1, 2, 0.5, 3, 25, 200, 2, 100],
 "ingredients_metric":["", "ml", "tsp", "tbsp", "tsp", "", "g", "g", "tbsp", "g"],
 "tags":["breakfast",
         "easy"],
 "images":["http://kissmybroccoliblog.com/wp-content/uploads/2012/08/IMG_2622.jpg"],
 "category":"breakfast",
 "prep_time":10,
 "cook_time":20 
 }

jdata = json.dumps(a)
print (jdata)