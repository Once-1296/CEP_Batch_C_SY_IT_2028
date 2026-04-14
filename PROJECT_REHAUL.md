# Overview

You are an expert backend developer specialising in API routing, database changes, and security first designs.

Recently there are some changes to the overall directory that you need to implement as mentiuoned below

## 1. New schema

Refer to [!new_schema.sql](new_schema.sql) for referring to the changed schema , appropriately update the backend/app folder to adjust the change. 

## 2. backend improvement

Create a make_admin.py file that allows us to create admins locally. and give admin the power to add pharmacists as well as patients.

As for pharmacist, it can see each patients name and id, and can ask for access to a patient details. Similarly on patient side, they can accept this request and see their reports

Main idea is pharmacist -> asks patient data access -> patient accepts -> pharmacist can see patient data -> sees abdm data and current_medications  -> suggests changes and such

If needed give a modified new_schema.sql, complete with drop...cascade statements at top to adjust for the above features

Remove any mock data present.

also in frontend add a small change which fetches API_BASE_URL from .env , and if it is None uses localhost:8000

## 3. nlp side

Based on the updated table schema, change the nlp part so that it can accurately use the newer details.  