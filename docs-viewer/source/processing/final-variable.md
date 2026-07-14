---
doc_id: final-variable
title: final variable
added_date: "2026-07-14 17:38"
last_updated: "2026-07-14 17:38"
parent_id: unsorted
---
# final variable

# final **variable**

In Java, marking a variable as **final** means that once it has been assigned a value, that variable’s reference cannot be changed. Here are a few key points:
	•	**Constant Value:** For primitive types, the value cannot be modified after assignment.
	•	**Immutable Reference:** For object references, the reference itself cannot point to a different object later, though the object’s internal state may still be mutable.
	•	**Use Cases:** It’s often used to create constants (often combined with static) or to ensure that a variable is not accidentally re-assigned, which is particularly useful in inner classes and anonymous functions.

For example:

final int myConstant = 5;
*// myConstant = 6; // This would cause a compilation error.*

final ArrayList<String> list = new ArrayList<String>();
list.add("Hello"); *// Allowed, because we're not reassigning list, we're modifying its contents.*
*// list = new ArrayList<String>(); // Not allowed; can't reassign a final reference.*

In short, **final** enforces that once a variable is set, it cannot be re-assigned to another value.
