import aiohttp
import asyncio
import json
import time
import os
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import logging
from tqdm.asyncio import tqdm
import urllib.parse
import random
from dataclasses import dataclass
from enum import Enum

class ReviewFilter(Enum):
    """Available filter options for Steam reviews."""
    RECENT = "recent"  # Sort by creation date
    UPDATED = "updated"  # Sort by last update date
    ALL = "all"  # Sort by helpfulness (not recommended for pagination)

@dataclass
class ReviewQueryParams:
    """Parameters for Steam review API queries."""
    filter: ReviewFilter = ReviewFilter.RECENT
    language: str = ""  # Empty means all languages
    day_range: int = 0  # Only used with filter=all
    cursor: str = "*"
    review_type: str = "all"  # all, positive, or negative
    purchase_type: str = "all"  # all, steam, or non_steam_purchase
    num_per_page: int = 100
    filter_offtopic: int = 1  # Set to 0 to include review bombs

class SteamDataCollector:
    def __init__(self, output_file: str, checkpoint_file: str):
        # Initialize file paths and create data directory
        self.output_file = output_file
        self.checkpoint_file = checkpoint_file
        self.partial_data_dir = os.path.join(os.path.dirname(output_file), "partial_data")
        os.makedirs(self.partial_data_dir, exist_ok=True)
        
        self.session = None
        self.processed_ids = set()
        self.in_progress_ids = set()
        
        # Configure logging with more detailed format
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
            handlers=[
                logging.FileHandler('steam_collection.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Track statistics with more detail
        self.stats = {
            'total_processed': 0,
            'successful_games': 0,
            'failed_games': 0,
            'total_reviews_collected': 0,
            'rate_limited_count': 0,
            'start_time': time.time(),
            'last_request_time': 0
        }

    async def initialize(self):
        """Initialize session with custom timeout and headers."""
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        self.session = aiohttp.ClientSession(timeout=timeout, headers=headers)
        self.processed_ids = self.load_processed_ids()
        self.in_progress_ids = self.load_in_progress_ids()
        self.logger.info(f"Initialized with {len(self.processed_ids)} completed and "
                        f"{len(self.in_progress_ids)} in-progress games")

    def load_processed_ids(self) -> set:
        """Load completely processed app IDs."""
        if os.path.exists(self.checkpoint_file):
            with open(self.checkpoint_file, 'r') as f:
                return {line.strip() for line in f}
        return set()

    def load_in_progress_ids(self) -> set:
        """Load IDs of games that were started but not completed."""
        return {filename.replace('reviews_', '').replace('.json', '')
                for filename in os.listdir(self.partial_data_dir)
                if filename.startswith('reviews_')}

    def save_checkpoint(self, appid: str, in_progress: bool = False):
        """Save an appid to the appropriate checkpoint file."""
        if in_progress:
            self.in_progress_ids.add(appid)
        else:
            self.in_progress_ids.discard(appid)
            self.processed_ids.add(appid)
            with open(self.checkpoint_file, 'a') as f:
                f.write(f"{appid}\n")
                f.flush()

    def get_partial_reviews_path(self, appid: str) -> str:
        """Get path for partial reviews data file."""
        return os.path.join(self.partial_data_dir, f"reviews_{appid}.json")

    def load_partial_reviews(self, appid: str) -> Tuple[List[Dict], str, int]:
        """Load partial review data for a game."""
        partial_file = self.get_partial_reviews_path(appid)
        if os.path.exists(partial_file):
            try:
                with open(partial_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return (
                        data.get('reviews', []),
                        data.get('next_cursor', '*'),
                        data.get('pages_collected', 0)
                    )
            except Exception as e:
                self.logger.warning(f"Error loading partial reviews for {appid}: {e}")
        return [], '*', 0

    def save_partial_reviews(self, appid: str, reviews: List[Dict], 
                           cursor: str, pages: int, error: Optional[str] = None):
        """Save partial review collection progress."""
        partial_file = self.get_partial_reviews_path(appid)
        data = {
            'reviews': reviews,
            'next_cursor': cursor,
            'pages_collected': pages,
            'last_updated': datetime.now().isoformat()
        }
        if error:
            data['error'] = str(error)
            
        with open(partial_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        if not error:
            self.save_checkpoint(appid, in_progress=True)

    async def enforce_rate_limit(self):
        """Ensure we don't exceed Steam's rate limits."""
        # Maintain at least 1 second between requests
        now = time.time()
        if now - self.stats['last_request_time'] < 1:
            delay = random.uniform(1.0, 2.0)  # Random delay between 1-2 seconds
            await asyncio.sleep(delay)
        self.stats['last_request_time'] = time.time()

    def build_review_url(self, appid: str, params: ReviewQueryParams) -> str:
        """Build the Steam review API URL with all parameters."""
        base_url = f"https://store.steampowered.com/appreviews/{appid}"
        
        query_params = {
            'json': 1,
            'filter': params.filter.value,
            'review_type': params.review_type,
            'purchase_type': params.purchase_type,
            'num_per_page': params.num_per_page,
            'cursor': urllib.parse.quote(params.cursor),
            'filter_offtopic_activity': params.filter_offtopic
        }
        
        # Only add language if specified
        if params.language:
            query_params['language'] = params.language
            
        # Only add day_range if using filter=all
        if params.filter == ReviewFilter.ALL and params.day_range > 0:
            query_params['day_range'] = params.day_range
            
        # Build query string
        query_string = '&'.join(f"{k}={v}" for k, v in query_params.items())
        return f"{base_url}?{query_string}"

    async def get_reviews(self, appid: str, max_reviews: int = 500) -> List[Dict]:
        """
        Fetch reviews with robust resume capability and consistent pagination.
        
        Args:
            appid: Steam app ID
            max_reviews: Maximum number of reviews to collect (default 500)
            
        Returns:
            List of review dictionaries
        """
        # Load any existing progress
        reviews, cursor, review_pages = self.load_partial_reviews(appid)
        start_time = time.time()
        
        if reviews:
            self.logger.info(f"Resuming review collection for {appid} from page {review_pages + 1} "
                           f"(found {len(reviews)} existing reviews)")
        else:
            self.logger.info(f"Starting fresh review collection for {appid}")

        # Initialize query parameters
        params = ReviewQueryParams(
            filter=ReviewFilter.RECENT,  # Use recent filter for consistent pagination
            num_per_page=100,  # Maximum allowed by Steam
            cursor=cursor
        )
        
        try:
            while len(reviews) < max_reviews:
                review_pages += 1
                page_start = time.time()
                
                # Enforce rate limiting
                await self.enforce_rate_limit()
                
                url = self.build_review_url(appid, params)
                self.logger.debug(f"Fetching reviews from: {url}")
                
                try:
                    async with self.session.get(url) as response:
                        if response.status == 429:  # Rate limited
                            wait_time = int(response.headers.get('Retry-After', 30))
                            self.logger.warning(f"Rate limited, waiting {wait_time}s...")
                            self.stats['rate_limited_count'] += 1
                            # Save progress before waiting
                            self.save_partial_reviews(appid, reviews, params.cursor, review_pages)
                            await asyncio.sleep(wait_time)
                            continue
                            
                        response.raise_for_status()
                        data = await response.json()
                    
                    if not data.get('success') or 'reviews' not in data:
                        self.logger.warning(f"No more reviews available for {appid}")
                        break
                        
                    new_reviews = data['reviews']
                    if not new_reviews:  # Empty page means we've reached the end
                        break
                        
                    reviews.extend(new_reviews)
                    
                    # Update cursor for next page
                    params.cursor = data.get('cursor', '')
                    if not params.cursor or params.cursor == '*':
                        self.logger.info(f"No more pages available for {appid}")
                        break
                    
                    # Save progress after each page
                    self.save_partial_reviews(appid, reviews, params.cursor, review_pages)
                    
                    page_time = time.time() - page_start
                    self.logger.info(f"Page {review_pages} completed in {page_time:.2f}s "
                                   f"(got {len(new_reviews)} reviews)")
                    
                    # Check query summary for total reviews
                    query_summary = data.get('query_summary', {})
                    total_reviews = query_summary.get('total_reviews', 0)
                    if len(reviews) >= total_reviews:
                        self.logger.info(f"Collected all available reviews for {appid}")
                        break
                    
                except aiohttp.ClientError as e:
                    self.logger.error(f"HTTP error for {appid} on page {review_pages}: {e}")
                    # Save progress and retry after delay
                    self.save_partial_reviews(appid, reviews, params.cursor, review_pages,
                                           error=str(e))
                    await asyncio.sleep(5)
                    continue
                
                # Small delay between pages
                await asyncio.sleep(random.uniform(1.0, 2.0))
            
            # Successfully got all reviews - clean up partial file
            partial_file = self.get_partial_reviews_path(appid)
            if os.path.exists(partial_file):
                os.remove(partial_file)
            
            total_time = time.time() - start_time
            self.logger.info(f"Completed review collection for {appid} "
                           f"({len(reviews)} reviews in {total_time:.2f}s)")
            
            # Sort reviews by helpfulness for storage
            return sorted(reviews, 
                        key=lambda x: (x.get('votes_up', 0), 
                                     -x.get('timestamp_created', 0)), 
                        reverse=True)[:max_reviews]
            
        except Exception as e:
            self.logger.error(f"Error collecting reviews for {appid}: {e}")
            # Save progress on error
            if reviews:
                self.save_partial_reviews(appid, reviews, params.cursor, review_pages, 
                                       error=str(e))
            return reviews

    async def process_game(self, appid: str) -> bool:
        """Process a single game with resume support."""
        try:
            # Skip if fully processed
            if appid in self.processed_ids:
                self.logger.debug(f"Skipping completed game {appid}")
                return False
                
            # Check if we have partial progress
            has_partial = appid in self.in_progress_ids
            if has_partial:
                self.logger.info(f"Resuming partially processed game {appid}")
            
            # Get store data
            start_time = time.time()
            self.logger.info(f"Fetching store data for {appid}...")
            
            await self.enforce_rate_limit()
            
            store_url = f"https://store.steampowered.com/api/appdetails?appids={appid}"
            async with self.session.get(store_url) as response:
                if response.status != 200:
                    self.logger.warning(f"No store data for {appid}")
                    return False
                    
                data = await response.json()
                if not data or not data.get(str(appid), {}).get('success'):
                    return False
                
                store_data = data[str(appid)]['data']
                if store_data.get('type') != 'game':
                    self.logger.info(f"Skipping {appid}: not a game")
                    return False

            game_name = store_data.get('name', 'Unknown')
            self.logger.info(f"Got store data for {game_name} ({time.time() - start_time:.2f}s)")

            # Get reviews
            self.logger.info(f"Fetching reviews for {game_name}...")
            reviews = await self.get_reviews(appid)

            # Save complete game data
            game_info = {
                'appid': appid,
                'name': game_name,
                'short_description': store_data.get('short_description'),
                'detailed_description': store_data.get('detailed_description'),
                'release_date': store_data.get('release_date', {}).get('date'),
                'developers': store_data.get('developers'),
                'publishers': store_data.get('publishers'),
                'header_image': store_data.get('header_image'),
                'website': store_data.get('website'),
                'store_data': store_data,
                'reviews': reviews,
                'collection_timestamp': datetime.now().isoformat(),
                'review_stats': {
                    'total_collected': len(reviews),
                    'positive_count': sum(1 for r in reviews if r.get('voted_up', False)),
                    'has_steam_purchase': sum(1 for r in reviews if r.get('steam_purchase', False))
                }
            }

            # Write to output file with proper encoding and formatting
            with open(self.output_file, 'a', encoding='utf-8') as f:
                json.dump(game_info, f, ensure_ascii=False, indent=None)
                f.write('\n')
                f.flush()  # Ensure immediate write to disk

            # Mark as fully completed
            self.save_checkpoint(appid, in_progress=False)
            self.stats['successful_games'] += 1
            self.stats['total_reviews_collected'] += len(reviews)

            self.logger.info(f"Successfully processed {game_name} ({len(reviews)} reviews)")
            return True

        except aiohttp.ClientError as e:
            self.logger.error(f"Network error processing {appid}: {e}")
            self.stats['failed_games'] += 1
            return False
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON parsing error for {appid}: {e}")
            self.stats['failed_games'] += 1
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error processing {appid}: {e}")
            self.stats['failed_games'] += 1
            return False

    async def process_batch(self, appids: List[str], batch_size: int = 5) -> Tuple[int, int]:
        """
        Process a batch of games with progress tracking and rate limiting.
        
        Args:
            appids: List of Steam app IDs to process
            batch_size: Number of games to process concurrently
            
        Returns:
            Tuple of (successful_count, failed_count)
        """
        tasks = []
        total = 0
        batch_start = time.time()
        
        for i in range(0, len(appids), batch_size):
            batch = appids[i:i + batch_size]
            self.logger.info(f"\nProcessing batch of {len(batch)} games...")
            
            # Process games concurrently within batch size limit
            results = await asyncio.gather(
                *[self.process_game(appid) for appid in batch],
                return_exceptions=True
            )
            
            # Count successes and handle any exceptions
            successes = sum(1 for r in results if isinstance(r, bool) and r)
            failures = sum(1 for r in results if isinstance(r, Exception) or 
                         (isinstance(r, bool) and not r))
            
            tasks.extend([r for r in results if isinstance(r, bool)])
            total += len(batch)
            
            # Calculate and log statistics
            elapsed = time.time() - batch_start
            speed = total / elapsed if elapsed > 0 else 0
            
            self.logger.info("\nBatch Statistics:")
            self.logger.info(f"- Processed: {len(batch)}")
            self.logger.info(f"- Speed: {speed:.1f} games/second")
            self.logger.info(f"- Successes: {successes}")
            self.logger.info(f"- Failures: {failures}")
            
            # Log any exceptions that occurred
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    self.logger.error(f"Error processing {batch[i]}: {result}")
            
            # Rate limiting between batches
            await asyncio.sleep(random.uniform(2.0, 3.0))
            
        return (
            sum(1 for t in tasks if isinstance(t, bool) and t),
            sum(1 for t in tasks if isinstance(t, bool) and not t)
        )

    async def run(self, limit: Optional[int] = None):
        """
        Main execution with comprehensive progress tracking and error handling.
        
        Args:
            limit: Optional limit on number of games to process
        """
        try:
            await self.initialize()
            
            # Get all Steam apps
            self.logger.info("Fetching list of Steam apps...")
            async with self.session.get(
                "https://api.steampowered.com/ISteamApps/GetAppList/v2/"
            ) as response:
                data = await response.json()
                apps = data['applist']['apps']
            
            total_apps = len(apps)
            self.logger.info(f"Found {total_apps} Steam apps")

            if limit:
                apps = apps[:limit]
                self.logger.info(f"Limited to first {limit} apps")
                
            # Process games
            appids = [str(app['appid']) for app in apps]
            batches = (len(appids) + 49) // 50  # Calculate total number of batches
            
            self.logger.info(f"\nStarting collection:")
            self.logger.info(f"- Apps to process: {len(appids)}")
            self.logger.info(f"- Total batches: {batches}")
            self.logger.info(f"- Already completed: {len(self.processed_ids)}")
            self.logger.info(f"- In progress: {len(self.in_progress_ids)}")
            
            # Process in batches with progress bar
            async for batch in tqdm(
                [appids[i:i+50] for i in range(0, len(appids), 50)],
                desc="Processing games",
                total=batches,
                unit="batch"
            ):
                successes, failures = await self.process_batch(batch)
                self.stats['total_processed'] += len(batch)
                
                # Show detailed progress
                elapsed = time.time() - self.stats['start_time']
                progress = (self.stats['total_processed'] / len(appids)) * 100
                speed = self.stats['total_processed'] / elapsed if elapsed > 0 else 0
                
                self.logger.info("\nProgress Summary:")
                self.logger.info(f"- Progress: {progress:.1f}% ({self.stats['total_processed']}/{len(appids)})")
                self.logger.info(f"- Successful games: {self.stats['successful_games']}")
                self.logger.info(f"- Failed games: {self.stats['failed_games']}")
                self.logger.info(f"- Reviews collected: {self.stats['total_reviews_collected']}")
                self.logger.info(f"- Processing speed: {speed:.2f} games/second")
                self.logger.info(f"- Runtime: {elapsed/3600:.1f} hours")
                self.logger.info(f"- Rate limit hits: {self.stats['rate_limited_count']}")
                
                if speed > 0:
                    remaining = len(appids) - self.stats['total_processed']
                    eta = remaining / speed
                    self.logger.info(f"- Estimated time remaining: {eta/3600:.1f} hours")

            # Final summary
            final_time = time.time() - self.stats['start_time']
            self.logger.info("\nCollection Complete!")
            self.logger.info(f"Final Statistics:")
            self.logger.info(f"- Total runtime: {final_time/3600:.1f} hours")
            self.logger.info(f"- Total processed: {self.stats['total_processed']}")
            self.logger.info(f"- Successful games: {self.stats['successful_games']}")
            self.logger.info(f"- Failed games: {self.stats['failed_games']}")
            self.logger.info(f"- Total reviews: {self.stats['total_reviews_collected']}")
            self.logger.info(f"- Total rate limits: {self.stats['rate_limited_count']}")
            if self.stats['successful_games'] > 0:
                self.logger.info(f"- Average reviews per game: "
                               f"{self.stats['total_reviews_collected']/self.stats['successful_games']:.1f}")

        except Exception as e:
            self.logger.error(f"Fatal error: {e}")
            raise
        finally:
            await self.close()
            self.logger.info("Resources cleaned up")

    async def close(self):
        """Clean up resources."""
        if self.session:
            await self.session.close()

async def main():
    """Entry point with command line argument handling."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced Steam Games Data Collector")
    parser.add_argument("--limit", type=int, help="Limit number of apps to process")
    parser.add_argument("--output", type=str, default="data/steam_games_data.jsonl",
                       help="Output file path")
    parser.add_argument("--checkpoint", type=str, default="data/processed_ids.txt",
                       help="Checkpoint file path")
    parser.add_argument("--batch-size", type=int, default=5,
                       help="Games to process concurrently (default: 5)")
    args = parser.parse_args()

    # Create directories
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    os.makedirs(os.path.dirname(args.checkpoint), exist_ok=True)

    collector = SteamDataCollector(args.output, args.checkpoint)
    
    try:
        await collector.run(limit=args.limit)
    except KeyboardInterrupt:
        print("\nDetected interrupt, cleaning up...")
        await collector.close()
        print("Progress saved. You can resume later.")
    except Exception as e:
        print(f"Fatal error: {e}")
        await collector.close()
        raise

if __name__ == "__main__":
    asyncio.run(main())