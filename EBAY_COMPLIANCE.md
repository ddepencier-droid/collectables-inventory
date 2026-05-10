# eBay API Compliance Documentation

## Application: Collectables Inventory Management

**Status**: Fully Compliant with eBay Marketplace Account Deletion Requirements  
**Last Updated**: May 9, 2026

---

## Implemented Endpoints

### 1. Challenge/Response Validation Endpoint

**URL**: `GET /api/ebay/marketplace-account-deletion`

**Purpose**: Validates endpoint ownership using SHA-256 challenge-response authentication

**Implementation**:
- Accepts `challenge_code` query parameter
- Returns SHA-256 hash of: `challenge_code + verification_token + endpoint_url`
- Used by eBay during initial setup verification

**Example Request**:
```
GET https://collectables-inventory-prod.railway.app/api/ebay/marketplace-account-deletion?challenge_code=ABC123
```

**Example Response**:
```json
{
  "challengeResponse": "7b3b718aa1075a526e9d9e793c2156c61018776a7df4355aad372be20504b090"
}
```

**Status Code**: 200 OK

---

### 2. Marketplace Account Deletion Notification Endpoint

**URL**: `POST /api/ebay/marketplace-account-deletion`

**Purpose**: Receives user account deletion requests from eBay and deletes all associated data

**Implementation**:
- Accepts JSON payload with marketplace account deletion notification
- Validates notification topic is `MARKETPLACE_ACCOUNT_DELETION`
- Extracts user identifiers: `username`, `userId`, `eiasToken`
- Deletes all data associated with the user
- Returns 200 OK to acknowledge receipt

**Example Request**:
```json
POST https://collectables-inventory-prod.railway.app/api/ebay/marketplace-account-deletion
Content-Type: application/json

{
  "metadata": {
    "topic": "MARKETPLACE_ACCOUNT_DELETION"
  },
  "notification": {
    "data": {
      "username": "ebay_user",
      "userId": "12345",
      "eiasToken": "token_value"
    }
  }
}
```

**Response**:
```
HTTP/1.1 200 OK
```

---

## Security Features

✅ **SHA-256 Challenge-Response Authentication**
- Endpoint ownership verified using cryptographic hashing
- Verification token stored securely in environment variables
- Challenge code + token + URL hashed to prevent replay attacks

✅ **Data Validation**
- Notification topic validation (must be `MARKETPLACE_ACCOUNT_DELETION`)
- User identifier validation (requires at least one: username, userId, or eiasToken)
- Proper error handling and logging

✅ **Compliance with eBay Requirements**
- Handles challenge verification requests correctly
- Processes account deletion notifications securely
- Acknowledges receipt with appropriate HTTP status codes
- Deletes all user-associated data per GDPR/privacy requirements

---

## Configuration

**Environment Variables Required**:
```
EBAY_NOTIFICATION_VERIFICATION_TOKEN=<token_provided_by_ebay>
EBAY_CLIENT_ID=<your_client_id>
EBAY_CLIENT_SECRET=<your_client_secret>
```

---

## Testing & Verification

**Challenge Endpoint Test**: ✅ PASSED
- Responds with valid SHA-256 hash
- Returns HTTP 200 OK
- Proper error handling for missing parameters

**Notification Endpoint Test**: ✅ PASSED
- Accepts marketplace account deletion notifications
- Validates topic and user identifiers
- Returns HTTP 200 OK

---

## Deployment Information

**Production URL**: 
```
https://collectables-inventory-prod.railway.app
```

**Repository**: 
```
https://github.com/ddepencier-droid/collectables-inventory
```

**Language**: Python 3.x  
**Framework**: Flask  
**Server**: Gunicorn (production WSGI server)

---

## Support

For questions about this compliance implementation, please refer to:
- `app.py` lines 2292-2370: eBay account deletion endpoint implementation
- Repository: https://github.com/ddepencier-droid/collectables-inventory
- Documentation: See DEPLOYMENT.md for deployment details

---

**This application fully implements eBay's mandatory Marketplace Account Deletion requirements and is ready for production use.**
