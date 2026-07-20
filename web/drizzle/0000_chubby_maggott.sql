CREATE TABLE `billing_users` (
	`id` text PRIMARY KEY NOT NULL,
	`email` text NOT NULL,
	`display_name` text,
	`stripe_customer_id` text,
	`created_at` text DEFAULT CURRENT_TIMESTAMP NOT NULL,
	`updated_at` text DEFAULT CURRENT_TIMESTAMP NOT NULL
);
--> statement-breakpoint
CREATE UNIQUE INDEX `billing_users_email_idx` ON `billing_users` (`email`);--> statement-breakpoint
CREATE UNIQUE INDEX `billing_users_stripe_customer_idx` ON `billing_users` (`stripe_customer_id`);--> statement-breakpoint
CREATE TABLE `legal_acceptances` (
	`id` text PRIMARY KEY NOT NULL,
	`user_id` text NOT NULL,
	`terms_version` text NOT NULL,
	`privacy_version` text NOT NULL,
	`accepted_at` text DEFAULT CURRENT_TIMESTAMP NOT NULL
);
--> statement-breakpoint
CREATE TABLE `stripe_events` (
	`event_id` text PRIMARY KEY NOT NULL,
	`event_type` text NOT NULL,
	`event_created` integer NOT NULL,
	`processed_at` text DEFAULT CURRENT_TIMESTAMP NOT NULL
);
--> statement-breakpoint
CREATE TABLE `subscriptions` (
	`stripe_subscription_id` text PRIMARY KEY NOT NULL,
	`user_id` text NOT NULL,
	`stripe_customer_id` text NOT NULL,
	`price_id` text NOT NULL,
	`plan` text DEFAULT 'pro' NOT NULL,
	`status` text NOT NULL,
	`current_period_end` integer NOT NULL,
	`grace_until` integer NOT NULL,
	`cancel_at_period_end` integer DEFAULT false NOT NULL,
	`event_created` integer NOT NULL,
	`updated_at` text DEFAULT CURRENT_TIMESTAMP NOT NULL
);
--> statement-breakpoint
CREATE INDEX `subscriptions_user_idx` ON `subscriptions` (`user_id`);--> statement-breakpoint
CREATE INDEX `subscriptions_customer_idx` ON `subscriptions` (`stripe_customer_id`);