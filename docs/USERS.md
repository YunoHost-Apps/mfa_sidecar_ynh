# MFA Sidecar Users Guide

This guide is for normal users of MFA Sidecar-protected apps.

## What MFA Sidecar is from a user perspective

MFA Sidecar is the login/MFA layer you may see before reaching certain protected apps.

If an app is protected, you will be redirected to the sidecar portal, asked to authenticate, and then sent back to the app you were trying to open.

## What you will see

### If the app is bypassed

You go straight to the app.

### If the app is protected

You are redirected to the sidecar portal.

There you will:

1. enter your sidecar username/email and password
2. complete MFA enrollment if needed
3. complete MFA verification on future logins
4. return to the original app after successful authentication

## Remembered sessions

The server operator can configure how long remembered sessions last.

That means you may not need to log in every single time.

However, you may still be asked to log in again if:

- your remembered session expires
- the operator clears active sessions
- your password is reset
- your MFA enrollment is reset
- the sidecar is restarted in a way that invalidates sessions

## Password resets

If an admin resets your password, use the new password they provide the next time you sign in.

## MFA resets

If an admin resets your MFA enrollment, you will need to enroll again on your next login.

This is normal after:

- losing a phone/device
- switching authenticators
- recovery from broken enrollment

## What to do if sign-in fails

Try these in order:

1. use a private/incognito browser window
2. try the portal again directly
3. contact the server operator

When you contact the operator, include:

- which app you were trying to open
- the URL if possible
- whether you reached the portal
- whether password worked
- whether MFA failed during enrollment or verification

## What an admin can do for you

An administrator can:

- reset your password
- reset your MFA enrollment
- disable or re-enable your sidecar account
- clear active sessions for everyone

They should not have to edit server files manually just to help you sign in.

## Important scope note

MFA Sidecar is a protection layer in front of apps. It is not necessarily the same thing as the app’s own internal account model.

The sidecar controls whether you may pass through to the protected app. The downstream app may still have its own login, permissions, or roles.

## Summary

The intended experience is simple:

- open app
- get redirected if protected
- sign in
- complete MFA
- return to app

If it feels much messier than that, the operator should probably investigate.
