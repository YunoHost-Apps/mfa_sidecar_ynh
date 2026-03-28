# MFA Sidecar User Guide

This guide is for normal users of MFA Sidecar-protected apps.

If you are not the server operator, the most important thing to know is simple:

- when a protected app needs authentication, you will be sent to the sidecar portal
- after login and MFA, you will be sent back to the app you were trying to open

## What you will see

When you try to open a protected app, one of two things happens:

### If the app is bypassed

You go straight to the app.

### If the app is protected

You are redirected to the MFA Sidecar portal.

There you will:

1. enter your sidecar username/email and password
2. complete MFA enrollment if required
3. complete MFA verification on future logins
4. be returned to the app you originally requested

## Remembered sessions

The server operator can configure how long remembered sessions last.

That means you may not need to perform a full login/MFA cycle on every single visit.

However, you can still be asked to log in again if:

- your remembered session expires
- the operator clears active sessions
- your password is reset
- your MFA enrollment is reset
- the sidecar is updated or restarted in a way that invalidates sessions

## Password resets

If your password is reset by an admin, your next login should use the new password they provide you.

## MFA resets

If your MFA enrollment is reset by an admin, you will need to enroll again the next time you sign in.

This is normal after:

- losing a phone/security device
- switching authenticators
- recovery from a broken enrollment

## What to do if you get stuck

If login or MFA stops working:

1. try a private/incognito browser window
2. try the portal again directly
3. contact the server operator

Useful things to tell the operator:

- which app you were trying to open
- the exact URL if possible
- whether you reached the portal at all
- whether password worked
- whether MFA failed during enrollment or verification

## What the admin can do for you

An administrator can:

- reset your password
- reset your MFA enrollment
- disable or re-enable your sidecar account
- clear active sessions for everyone

They should **not** need to edit server files by hand just to help you sign in.

## Privacy / scope

MFA Sidecar is a protection layer in front of apps. It is not automatically the same thing as your downstream app account.

The sidecar decides whether you may pass through to the protected app. The app itself may still have its own login, own permissions, or own user model depending on how that service works.

## Summary

For most users the experience should be:

- open app
- get redirected
- sign in once
- complete MFA
- return to app

If it feels more complicated than that, something is probably worth reporting to the operator.