CREATE TABLE `analytics_events` (
	`id` integer PRIMARY KEY AUTOINCREMENT NOT NULL,
	`event_day` text NOT NULL,
	`session_hash` text NOT NULL,
	`calculator_id` text NOT NULL,
	`event_name` text NOT NULL,
	`event_detail` text DEFAULT '' NOT NULL,
	`event_count` integer DEFAULT 1 NOT NULL,
	`first_seen_at` text DEFAULT CURRENT_TIMESTAMP NOT NULL,
	`last_seen_at` text DEFAULT CURRENT_TIMESTAMP NOT NULL
);
--> statement-breakpoint
CREATE UNIQUE INDEX `analytics_events_session_event_idx` ON `analytics_events` (`event_day`,`session_hash`,`calculator_id`,`event_name`,`event_detail`);--> statement-breakpoint
CREATE INDEX `analytics_events_day_calculator_idx` ON `analytics_events` (`event_day`,`calculator_id`);