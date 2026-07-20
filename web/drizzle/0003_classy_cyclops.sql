CREATE TABLE `preauthorized_entitlements` (
	`id` text PRIMARY KEY NOT NULL,
	`email` text NOT NULL,
	`plan` text DEFAULT 'pro' NOT NULL,
	`reason` text NOT NULL,
	`expires_at` integer,
	`granted_by` text NOT NULL,
	`granted_at` text DEFAULT CURRENT_TIMESTAMP NOT NULL,
	`claimed_at` text,
	`claimed_by_user_id` text,
	`revoked_at` text,
	`revoked_by` text,
	`terms_version` text NOT NULL,
	`privacy_version` text NOT NULL
);
--> statement-breakpoint
CREATE INDEX `preauthorized_entitlements_email_idx` ON `preauthorized_entitlements` (`email`);--> statement-breakpoint
CREATE INDEX `preauthorized_entitlements_claimed_user_idx` ON `preauthorized_entitlements` (`claimed_by_user_id`);--> statement-breakpoint
CREATE INDEX `preauthorized_entitlements_granted_at_idx` ON `preauthorized_entitlements` (`granted_at`);