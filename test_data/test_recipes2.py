import json 

a={"name": "Masala frittata with avocado salsa", 
 "description":"A spicy twist on a simple frittata recipe, with Masala paste, coriander and plump cherry tomatoes. Pair it with our avocado salsa for a light and budget-friendly supper.",
 "author":"Jemma Morphet",
 "steps":["Heat the oil in a medium non-stick, ovenproof frying pan. Tip in the sliced onions and cook over a medium heat for about 10 mins until soft and golden. Add the Madras paste and fry for 1 min more, then tip in half the tomatoes and half the chilli. Cook until the mixture is thick and the tomatoes have all burst.",
        "Heat the grill to high. Add half the coriander to the eggs and season, then pour over the spicy onion mixture. Stir gently once or twice, then cook over a low heat for 8-10 mins until almost set. Transfer to the grill for 3-5 mins until set.",
        "To make the salsa, mix the avocado, remaining chilli and tomatoes, chopped onion, remaining coriander and the lemon juice together, then season and serve with the frittata."],
 "ingredients":["rapeseed oil",
                "onions", "Madras curry paste", "cherry tomatoes, halved", "red chilli, deseeded and finely chopped",
                "small pack coriander, roughly chopped", "large eggs, beaten", "avocado, stoned, peeled and cubed",
                "lemon, juiced"],
 "ingredients_quant":[2, 3, 1, 500, 1, 1, 8, 1, 1],
 "ingredients_metric":["tbsp", "", "tbsp", "g", "", "", "", "", ""],
 "tags":["snack",
         "easy"],
 "images":["https://www.bbcgoodfood.com/sites/default/files/styles/recipe/public/recipe/recipe-image/2016/01/masala-frittata-with-avocado-salsa.jpg"],
 "category":"breakfast",
 "prep_time":15,
 "cook_time":25 
 }

jdata = json.dumps(a)
print (jdata)