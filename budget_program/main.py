from __future__ import annotations

from datetime import date

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from budget_program.db import init_db, is_onboarded, set_onboarded
from budget_program.services import (
    create_expense,
    create_income,
    dashboard_summary,
    default_checking_account_id,
    delete_item,
    list_rows,
    save_allocations,
    upsert_item,
)

app = FastAPI(title="Minimal Budget Hub")
app.mount("/static", StaticFiles(directory="budget_program/static"), name="static")
templates = Jinja2Templates(directory="budget_program/templates")


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    if not is_onboarded():
        return RedirectResponse("/onboarding/0", status_code=303)
    summary = dashboard_summary()
    return templates.TemplateResponse("dashboard.html", {"request": request, "summary": summary, "today": date.today().isoformat()})


@app.get("/onboarding/{step}", response_class=HTMLResponse)
def onboarding(request: Request, step: int):
    items = {
        "accounts": list_rows("accounts"),
        "debts": list_rows("debts"),
        "fixed_expenses": list_rows("fixed_expenses"),
    }
    return templates.TemplateResponse("onboarding.html", {"request": request, "step": step, **items})


@app.post("/onboarding/finish")
def finish_onboarding():
    set_onboarded()
    return RedirectResponse("/", status_code=303)


@app.post("/accounts/save")
def save_account(
    item_id: str = Form(""), name: str = Form(...), type: str = Form(...), starting_balance: float = Form(...)
):
    upsert_item("accounts", item_id or None, {"name": name, "type": type, "balance": starting_balance})
    return RedirectResponse("/onboarding/1", status_code=303)


@app.post("/debts/save")
def save_debt(
    item_id: str = Form(""),
    name: str = Form(...),
    balance: float = Form(...),
    minimum_payment: str = Form(""),
    interest_rate: str = Form(""),
):
    upsert_item(
        "debts",
        item_id or None,
        {
            "name": name,
            "balance": balance,
            "minimum_payment": float(minimum_payment) if minimum_payment else None,
            "interest_rate": float(interest_rate) if interest_rate else None,
        },
    )
    return RedirectResponse("/onboarding/2", status_code=303)


@app.post("/expenses/save")
def save_fixed_expense(item_id: str = Form(""), name: str = Form(...), amount_monthly: float = Form(...), due_day: str = Form("")):
    upsert_item(
        "fixed_expenses",
        item_id or None,
        {"name": name, "amount_monthly": amount_monthly, "due_day": int(due_day) if due_day else None},
    )
    return RedirectResponse("/onboarding/3", status_code=303)


@app.post("/{table}/delete/{item_id}")
def remove_item(table: str, item_id: str):
    mapping = {"accounts": 1, "debts": 2, "fixed_expenses": 3}
    delete_item(table, item_id)
    return RedirectResponse(f"/onboarding/{mapping.get(table,1)}", status_code=303)


@app.get("/manage/{section}", response_class=HTMLResponse)
def manage(request: Request, section: str):
    data = {
        "accounts": list_rows("accounts"),
        "debts": list_rows("debts"),
        "fixed_expenses": list_rows("fixed_expenses"),
        "allocations": list_rows("allocations"),
        "transactions": dashboard_summary()["transactions"],
    }
    return templates.TemplateResponse("manage.html", {"request": request, "section": section, **data})


@app.post("/allocations/save")
def allocations_save(rows: str = Form(...)):
    items = []
    if rows.strip():
        for row in rows.strip().splitlines():
            ttype, tid, pct = row.split(",")
            items.append({"target_type": ttype.strip(), "target_id": tid.strip(), "percent": float(pct.strip())})
    save_allocations(items)
    return RedirectResponse("/manage/allocations", status_code=303)


@app.post("/transactions/income")
def add_income(amount: float = Form(...), date_iso: str = Form(date.today().isoformat()), note: str = Form("")):
    create_income(amount, date_iso, note or None)
    return RedirectResponse("/", status_code=303)


@app.post("/transactions/expense")
def add_expense(
    amount: float = Form(...),
    date_iso: str = Form(...),
    note: str = Form(""),
    category: str = Form(""),
    account_id: str = Form(""),
):
    account = account_id or default_checking_account_id()
    create_expense(amount, date_iso, note or None, category or None, account)
    return RedirectResponse("/", status_code=303)
