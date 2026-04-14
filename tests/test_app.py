from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add the src directory to the path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app

client = TestClient(app)


class TestRootEndpoint:
    """Tests for the root endpoint"""
    
    def test_root_redirect(self):
        """Test that GET / redirects to /static/index.html"""
        # Arrange: No special setup needed
        
        # Act: Make GET request to root
        response = client.get("/", follow_redirects=False)
        
        # Assert: Check redirect status and location
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Tests for the GET /activities endpoint"""
    
    def test_get_all_activities(self):
        """Test that GET /activities returns all activities"""
        # Arrange: No special setup needed
        
        # Act: Make GET request to activities
        response = client.get("/activities")
        
        # Assert: Check response structure
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) > 0
        
        # Verify known activities exist
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
    
    def test_activity_structure(self):
        """Test that activities have the correct structure"""
        # Arrange: No special setup needed
        
        # Act: Get activities data
        response = client.get("/activities")
        data = response.json()
        
        # Assert: Check a specific activity structure
        chess_club = data["Chess Club"]
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club
        assert isinstance(chess_club["participants"], list)


class TestSignupForActivity:
    """Tests for the POST /activities/{activity_name}/signup endpoint"""
    
    def test_successful_signup(self):
        """Test successful signup for an activity"""
        # Arrange: Use a unique email to avoid conflicts
        email = "test_signup_success@mergington.edu"
        
        # Act: Make POST request to signup
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        
        # Assert: Check success response
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert "Chess Club" in data["message"]
    
    def test_signup_duplicate_student(self):
        """Test that signup fails if student is already registered"""
        # Arrange: Use an email that's already in Chess Club
        email = "michael@mergington.edu"
        
        # Act: Attempt to sign up again
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        
        # Assert: Check error response
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]
    
    def test_signup_nonexistent_activity(self):
        """Test that signup fails for non-existent activity"""
        # Arrange: Use a non-existent activity name
        activity_name = "Nonexistent Activity"
        email = "test_nonexistent@mergington.edu"
        
        # Act: Make POST request
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert: Check 404 response
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]
    
    def test_signup_data_persistence(self):
        """Test that signup data is persisted in the in-memory store"""
        # Arrange: Get initial participant count
        response_before = client.get("/activities")
        activities_before = response_before.json()
        chess_club_before = activities_before["Chess Club"]
        initial_count = len(chess_club_before["participants"])
        
        # Act: Sign up a new student
        new_email = "persistence_test@mergington.edu"
        client.post(
            "/activities/Chess Club/signup",
            params={"email": new_email}
        )
        
        # Assert: Check that participant was added
        response_after = client.get("/activities")
        activities_after = response_after.json()
        chess_club_after = activities_after["Chess Club"]
        final_count = len(chess_club_after["participants"])
        
        assert final_count == initial_count + 1
        assert new_email in chess_club_after["participants"]


class TestUnregisterFromActivity:
    """Tests for the DELETE /activities/{activity_name}/signup endpoint"""
    
    def test_successful_unregistration(self):
        """Test successful unregistration from an activity"""
        # Arrange: First sign up a student
        email = "test_unregister@mergington.edu"
        client.post("/activities/Chess Club/signup", params={"email": email})
        
        # Act: Unregister the student
        response = client.delete(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        
        # Assert: Check success response
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert "Chess Club" in data["message"]
    
    def test_unregister_nonexistent_participant(self):
        """Test that unregister fails for non-existent participant"""
        # Arrange: Use an email not in the activity
        email = "nonexistent_participant@mergington.edu"
        
        # Act: Attempt to unregister
        response = client.delete(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        
        # Assert: Check 404 response
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]
    
    def test_unregister_nonexistent_activity(self):
        """Test that unregister fails for non-existent activity"""
        # Arrange: Use non-existent activity
        activity_name = "Nonexistent Activity"
        email = "test_unregister_nonexistent@mergington.edu"
        
        # Act: Make DELETE request
        response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert: Check 404 response
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]
    
    def test_unregister_data_persistence(self):
        """Test that unregister data is persisted in the in-memory store"""
        # Arrange: Sign up a student first
        email = "persistence_unregister@mergington.edu"
        client.post("/activities/Chess Club/signup", params={"email": email})
        
        # Get count before unregister
        response_before = client.get("/activities")
        activities_before = response_before.json()
        initial_count = len(activities_before["Chess Club"]["participants"])
        
        # Act: Unregister the student
        client.delete("/activities/Chess Club/signup", params={"email": email})
        
        # Assert: Check that participant was removed
        response_after = client.get("/activities")
        activities_after = response_after.json()
        final_count = len(activities_after["Chess Club"]["participants"])
        
        assert final_count == initial_count - 1
        assert email not in activities_after["Chess Club"]["participants"]