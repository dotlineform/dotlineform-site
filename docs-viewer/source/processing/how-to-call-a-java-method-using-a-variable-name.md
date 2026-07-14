---
doc_id: how-to-call-a-java-method-using-a-variable-name
title: "how to call a java method using a variable name?"
added_date: "2026-07-14 17:38"
last_updated: "2026-07-14 17:38"
parent_id: unsorted
---
# how to call a java method using a variable name?



# [how to call a java method using a variable name?](https://stackoverflow.com/questions/4138527/how-to-call-a-java-method-using-a-variable-name#4138562)
Use reflection:


```
Method method = WhateverYourClassIs.class.getDeclaredMethod("Method" + MyVar);
method.invoke();

```
