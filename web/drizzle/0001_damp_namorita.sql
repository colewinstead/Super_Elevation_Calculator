ALTER TABLE `billing_users` ADD `identity_provider` text DEFAULT 'workos' NOT NULL;--> statement-breakpoint
ALTER TABLE `billing_users` ADD `identity_subject` text DEFAULT '' NOT NULL;--> statement-breakpoint
UPDATE `billing_users` SET `identity_provider` = 'legacy', `identity_subject` = `id` WHERE `identity_subject` = '';--> statement-breakpoint
CREATE UNIQUE INDEX `billing_users_identity_idx` ON `billing_users` (`identity_provider`,`identity_subject`);
