CREATE TABLE `manual_entitlements` (
	`id` text PRIMARY KEY NOT NULL,
	`user_id` text NOT NULL,
	`plan` text DEFAULT 'pro' NOT NULL,
	`reason` text NOT NULL,
	`expires_at` integer,
	`granted_by` text NOT NULL,
	`granted_at` text DEFAULT CURRENT_TIMESTAMP NOT NULL,
	`revoked_at` text,
	`revoked_by` text,
	`terms_version` text NOT NULL,
	`privacy_version` text NOT NULL
);
--> statement-breakpoint
CREATE INDEX `manual_entitlements_user_idx` ON `manual_entitlements` (`user_id`);--> statement-breakpoint
CREATE INDEX `manual_entitlements_granted_at_idx` ON `manual_entitlements` (`granted_at`);