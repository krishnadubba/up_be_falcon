import json 

a={"name": "Polenta & mushroom tart", 
 "description":"This pretty vegetarian main is made from quick-cook cheesy polenta topped with mushrooms, mozzarella, rocket and balsamic vinegar",
 "author":"Katy Gilhooly",
 "steps":["Heat oven to 200C/180C fan/gas 6. Grease and line a large baking tray with baking parchment.",
          "Bring the stock to the boil in a large saucepan, then slowly pour in the polenta, whisking all the time. Bring it to the boil and bubble for 8 mins, whisking continuously. Remove from the heat and stir in the cheese, butter, rosemary and plenty of seasoning. Spread the polenta over the lined tray and bake for 30 mins.",
        "Meanwhile, mix the mushrooms with the thyme and some seasoning. Heat a splash of oil in a large frying pan and fry the mushrooms in a couple of batches until golden. Tear the mozzarella into pieces and pat dry with kitchen paper.", 
        "Top the baked polenta with the mushrooms and mozzarella, then bake again for 10 mins or until the cheese is melted and bubbling. Scatter the rocket over the tart and drizzle with the balsamic vinegar.",
        ],
 "ingredients":["butter, plus extra for greasing",
                "vegetable stock", "quick-cook polenta", " Parmesan (or vegetarian alternative), grated",
                "rosemary sprigs, leaves finely chopped",
                "chestnut mushrooms, halved", "small bunch thyme, leaves only", 
                "olive oil", "ball mozzarella, drained", "large handful rocket", "balsamic vinegar"],
 "ingredients_quant":[25, 850, 200, 50, 2, 500, 1, 2, 125, 1, 1],
 "ingredients_metric":["g", "ml", "g", "", "g", "", "", "g", "", ""],
 "tags":["lunch",
         "easy", "veg"],
 "images":["https://www.bbcgoodfood.com/sites/default/files/styles/recipe/public/recipe_images/polenta-mushroom-tart.jpg"],
 "category":"lunch",
 "prep_time":10,
 "cook_time":40 
 }

jdata = json.dumps(a)
print (jdata)