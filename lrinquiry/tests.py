from datetime import date

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Contact, Inquiry
from .views import SEARCH_LIMIT, _distinct_values


class InquiryTestBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user("tester", password="pw12345678")
        cls.contact = Contact.objects.create(name="Jignesh", phone="9898011223")

    def setUp(self):
        self.client.login(username="tester", password="pw12345678")

    def payload(self, **overrides):
        data = {
            "inquiry_date": "2026-09-19",
            "party_name": "Shree Krishna Traders",
            "transport_name": "Gati Express",
            "bill_series": "GJ",
            "bill_no": "10482",
            "bill_date": "2026-09-15",
            "lr_no": "12",
            "contact_name": "Jignesh",
            "contact_phone": "9898011223",
            "remarks": "",
            "status": Inquiry.OPEN,
        }
        data.update(overrides)
        return data

    def make_inquiry(self, **kwargs):
        defaults = dict(
            inquiry_date=date(2026, 9, 19), party_name="P", transport_name="T",
            bill_series="GJ", bill_no="1", contact=self.contact,
        )
        defaults.update(kwargs)
        return Inquiry.objects.create(**defaults)


class BillDateAndCartoonTests(InquiryTestBase):
    def test_form_shows_bill_date_and_cartoon(self):
        html = self.client.get(reverse("inquiry_dashboard")).content.decode()
        self.assertIn(">Bill date</label>", html)
        self.assertIn(">Cartoon</label>", html)
        self.assertNotIn(">LR no</label>", html)
        self.assertNotIn("<th>LR no</th>", html)

    def test_bill_date_and_cartoon_are_saved(self):
        response = self.client.post(reverse("add_inquiry"), self.payload())
        self.assertEqual(response.status_code, 302)
        inquiry = Inquiry.objects.get()
        self.assertEqual(inquiry.bill_date, date(2026, 9, 15))
        self.assertEqual(inquiry.lr_no, "12")

    def test_bill_date_is_required_for_new_inquiry(self):
        response = self.client.post(reverse("add_inquiry"), self.payload(bill_date=""))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Inquiry.objects.count(), 0)

    def test_old_inquiry_without_bill_date_can_still_be_edited(self):
        inquiry = self.make_inquiry()
        self.assertIsNone(inquiry.bill_date)
        response = self.client.post(
            reverse("edit_inquiry", args=[inquiry.pk]),
            self.payload(bill_date="", bill_no="1", remarks="called"),
        )
        self.assertEqual(response.status_code, 302)
        inquiry.refresh_from_db()
        self.assertEqual(inquiry.remarks, "called")

    def test_edit_page_prefills_bill_date(self):
        inquiry = self.make_inquiry(bill_date=date(2026, 9, 15))
        html = self.client.get(reverse("edit_inquiry", args=[inquiry.pk])).content.decode()
        self.assertIn('value="2026-09-15"', html)

    def test_board_lists_bill_date(self):
        self.make_inquiry(bill_date=date(2026, 9, 15))
        html = self.client.get(reverse("inquiry_dashboard") + "?date=2026-09-19").content.decode()
        self.assertIn("15-09-2026", html)


class PerformanceGuardTests(InquiryTestBase):
    def test_distinct_values_returns_each_name_once(self):
        # Inquiry has a default ordering; a naive .distinct() used to return
        # one row per inquiry instead of one per name.
        for i in range(5):
            self.make_inquiry(bill_no=str(i), party_name="Same Party",
                              inquiry_date=date(2026, 9, 1 + i))
        self.assertEqual(_distinct_values("party_name"), ["Same Party"])

    def test_search_results_are_capped(self):
        Inquiry.objects.bulk_create([
            Inquiry(inquiry_date=date(2026, 9, 19), party_name="Bulk Party",
                    transport_name="T", bill_series="GJ", bill_no=str(i),
                    contact=self.contact)
            for i in range(SEARCH_LIMIT + 20)
        ])
        response = self.client.get(reverse("inquiry_dashboard"), {"q": "Bulk"})
        self.assertEqual(len(response.context["inquiries"]), SEARCH_LIMIT)
        self.assertTrue(response.context["truncated"])


class StatusUpdateTests(InquiryTestBase):
    def test_background_update_returns_json(self):
        inquiry = self.make_inquiry()
        response = self.client.post(
            reverse("update_inquiry_status", args=[inquiry.pk]),
            {"status": Inquiry.CLOSED},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.json(), {"ok": True, "status": "CLOSED", "label": "Solved"})
        inquiry.refresh_from_db()
        self.assertEqual(inquiry.status, Inquiry.CLOSED)

    def test_background_update_rejects_bad_status(self):
        inquiry = self.make_inquiry()
        response = self.client.post(
            reverse("update_inquiry_status", args=[inquiry.pk]),
            {"status": "NOPE"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 400)
        inquiry.refresh_from_db()
        self.assertEqual(inquiry.status, Inquiry.OPEN)

    def test_plain_form_post_still_redirects(self):
        inquiry = self.make_inquiry()
        response = self.client.post(
            reverse("update_inquiry_status", args=[inquiry.pk]),
            {"status": Inquiry.FOLLOWED},
        )
        self.assertEqual(response.status_code, 302)
        inquiry.refresh_from_db()
        self.assertEqual(inquiry.status, Inquiry.FOLLOWED)
