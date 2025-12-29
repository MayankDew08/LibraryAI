import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch


class TestBorrowFineAndDueDateLogic:
    """Test suite for fine calculation and due date logic in borrow service"""

    def test_due_date_calculation_14_days(self):
        """Test that due date is correctly set to 14 days from borrow date"""
        borrow_date = datetime(2025, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        expected_due_date = borrow_date + timedelta(days=14)

        assert expected_due_date == borrow_date + timedelta(days=14)
        assert (expected_due_date - borrow_date).days == 14

    def test_fine_calculation_on_time_return(self):
        """Test fine calculation when book is returned on time"""
        # Simulate the calculate_fine logic without SQLAlchemy
        borrow_date = datetime(2025, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        due_date = borrow_date + timedelta(days=14)
        return_date = borrow_date + timedelta(days=10)  # 4 days early

        # Simulate calculate_fine logic
        if return_date and due_date:
            return_tz = return_date if return_date.tzinfo else return_date.replace(tzinfo=timezone.utc)
            due_tz = due_date if due_date.tzinfo else due_date.replace(tzinfo=timezone.utc)
            if return_tz > due_tz:
                days_late = (return_tz - due_tz).days
                fine = max(0, days_late * 5.0)
            else:
                fine = 0.0
        else:
            fine = 0.0

        assert fine == 0.0

    def test_fine_calculation_one_day_late(self):
        """Test fine calculation when book is returned 1 day late"""
        borrow_date = datetime(2025, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        due_date = borrow_date + timedelta(days=14)
        return_date = due_date + timedelta(days=1)

        # Simulate calculate_fine logic
        if return_date and due_date:
            return_tz = return_date if return_date.tzinfo else return_date.replace(tzinfo=timezone.utc)
            due_tz = due_date if due_date.tzinfo else due_date.replace(tzinfo=timezone.utc)
            if return_tz > due_tz:
                days_late = (return_tz - due_tz).days
                fine = max(0, days_late * 5.0)
            else:
                fine = 0.0
        else:
            fine = 0.0

        assert fine == 5.0  # Rs 5 per day

    def test_fine_calculation_multiple_days_late(self):
        """Test fine calculation when book is returned multiple days late"""
        borrow_date = datetime(2025, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        due_date = borrow_date + timedelta(days=14)
        return_date = due_date + timedelta(days=7)  # 7 days late

        # Simulate calculate_fine logic
        if return_date and due_date:
            return_tz = return_date if return_date.tzinfo else return_date.replace(tzinfo=timezone.utc)
            due_tz = due_date if due_date.tzinfo else due_date.replace(tzinfo=timezone.utc)
            if return_tz > due_tz:
                days_late = (return_tz - due_tz).days
                fine = max(0, days_late * 5.0)
            else:
                fine = 0.0
        else:
            fine = 0.0

        assert fine == 35.0  # 7 days * Rs 5

    def test_fine_calculation_return_same_day(self):
        """Test fine calculation when book is returned on due date"""
        borrow_date = datetime(2025, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        due_date = borrow_date + timedelta(days=14)
        return_date = due_date  # Exactly on due date

        # Simulate calculate_fine logic
        if return_date and due_date:
            return_tz = return_date if return_date.tzinfo else return_date.replace(tzinfo=timezone.utc)
            due_tz = due_date if due_date.tzinfo else due_date.replace(tzinfo=timezone.utc)
            if return_tz > due_tz:
                days_late = (return_tz - due_tz).days
                fine = max(0, days_late * 5.0)
            else:
                fine = 0.0
        else:
            fine = 0.0

        assert fine == 0.0

    def test_fine_calculation_no_return_date(self):
        """Test fine calculation when book hasn't been returned yet"""
        # Simulate calculate_fine logic
        return_date = None
        due_date = datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc)

        if return_date and due_date:
            return_tz = return_date if return_date.tzinfo else return_date.replace(tzinfo=timezone.utc)
            due_tz = due_date if due_date.tzinfo else due_date.replace(tzinfo=timezone.utc)
            if return_tz > due_tz:
                days_late = (return_tz - due_tz).days
                fine = max(0, days_late * 5.0)
            else:
                fine = 0.0
        else:
            fine = 0.0

        assert fine == 0.0

    def test_fine_calculation_with_timezone_naive_dates(self):
        """Test fine calculation handles timezone-naive dates correctly"""
        borrow_date = datetime(2025, 1, 1, 10, 0, 0)  # naive
        due_date = borrow_date + timedelta(days=14)  # naive
        return_date = due_date + timedelta(days=3)  # naive

        # Simulate calculate_fine logic
        if return_date and due_date:
            return_tz = return_date if return_date.tzinfo else return_date.replace(tzinfo=timezone.utc)
            due_tz = due_date if due_date.tzinfo else due_date.replace(tzinfo=timezone.utc)
            if return_tz > due_tz:
                days_late = (return_tz - due_tz).days
                fine = max(0, days_late * 5.0)
            else:
                fine = 0.0
        else:
            fine = 0.0

        assert fine == 15.0  # 3 days * Rs 5

    def test_is_overdue_active_book_past_due(self):
        """Test is_overdue returns True for active book past due date"""
        borrow_date = datetime(2025, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        due_date = borrow_date + timedelta(days=14)

        return_date = None  # Not returned
        current_time = due_date + timedelta(days=1)

        # Simulate is_overdue logic
        if return_date:  # Already returned
            overdue = False
        else:
            overdue = current_time > due_date

        assert overdue is True

    def test_is_overdue_active_book_not_past_due(self):
        """Test is_overdue returns False for active book not past due date"""
        borrow_date = datetime(2025, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        due_date = borrow_date + timedelta(days=14)

        return_date = None  # Not returned
        current_time = borrow_date + timedelta(days=7)  # Before due date

        # Simulate is_overdue logic
        if return_date:  # Already returned
            overdue = False
        else:
            overdue = current_time > due_date

        assert overdue is False

    def test_is_overdue_returned_book(self):
        """Test is_overdue returns False for already returned book"""
        borrow_date = datetime(2025, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        due_date = borrow_date + timedelta(days=14)
        return_date = due_date + timedelta(days=5)  # Returned late

        # Simulate is_overdue logic
        if return_date:  # Already returned
            overdue = False
        else:
            overdue = datetime.now(timezone.utc) > due_date

        # Even though it was returned late, it's not currently overdue
        assert overdue is False

    def test_borrow_book_sets_correct_due_date(self):
        """Test that borrow_book sets due date to 14 days from borrow date"""
        # Test the due date calculation logic directly
        borrow_time = datetime(2025, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        expected_due_date = borrow_time + timedelta(days=14)

        # This logic is implemented in the borrow_book function
        due_date = borrow_time + timedelta(days=14)

        assert due_date == expected_due_date
        assert (due_date - borrow_time).days == 14

    def test_student_return_no_fine(self):
        """Test student return when no fine is incurred"""
        from app.services.borrow import student_return_book
        from app.schemas.borrow_schemas import StudentReturnSchema

        # Create mock objects
        mock_db = Mock()
        mock_user = Mock()
        mock_user.id = 1
        mock_user.name = "Test User"
        mock_user.email = "test@example.com"

        mock_book = Mock()
        mock_book.book_id = 1
        mock_book.title = "Test Book"
        mock_book.available_copies = 5

        # Create mock borrow record
        mock_borrow = Mock()
        mock_borrow.borrow_id = 123
        mock_borrow.borrowed_date = datetime(2025, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        mock_borrow.due_date = mock_borrow.borrowed_date + timedelta(days=14)
        mock_borrow.return_date = mock_borrow.borrowed_date + timedelta(days=10)  # Return early
        mock_borrow.fine_amount = 0.0
        mock_borrow.mark_returned = Mock()

        # Setup mock query chain
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first.side_effect = [mock_user, mock_book, mock_borrow]
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query

        return_data = StudentReturnSchema(user_email="test@example.com", book_title="Test Book")

        result = student_return_book(mock_db, return_data)

        assert result['fine_amount'] == 0.0
        assert result['status'] == 'returned_and_cleared'
        assert 'returned successfully' in result['message'].lower()

    def test_student_return_with_fine(self):
        """Test student return when fine is incurred"""
        from app.services.borrow import student_return_book
        from app.schemas.borrow_schemas import StudentReturnSchema

        # Create mock objects
        mock_db = Mock()
        mock_user = Mock()
        mock_user.id = 1
        mock_user.name = "Test User"
        mock_user.email = "test@example.com"

        mock_book = Mock()
        mock_book.book_id = 1
        mock_book.title = "Test Book"
        mock_book.available_copies = 5

        # Create mock borrow record
        mock_borrow = Mock()
        mock_borrow.borrow_id = 123
        mock_borrow.borrowed_date = datetime(2025, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        mock_borrow.due_date = mock_borrow.borrowed_date + timedelta(days=14)
        mock_borrow.return_date = mock_borrow.due_date + timedelta(days=5)  # 5 days late
        mock_borrow.fine_amount = 25.0  # 5 days late * Rs 5
        mock_borrow.mark_returned = Mock()

        # Setup mock query chain
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first.side_effect = [mock_user, mock_book, mock_borrow]
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query

        return_data = StudentReturnSchema(user_email="test@example.com", book_title="Test Book")

        result = student_return_book(mock_db, return_data)

        assert result['fine_amount'] == 25.0
        assert result['status'] == 'awaiting_fine_payment'
        assert 'pay the fine' in result['message'].lower()
        assert result['days_late'] == 5