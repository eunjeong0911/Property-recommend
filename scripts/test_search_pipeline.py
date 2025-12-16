#!/usr/bin/env python
"""
터미널 기반 검색 파이프라인 테스트 스크립트

Requirements:
- 7.1: 사용자 질문을 입력받아 전체 검색 파이프라인을 실행
- 7.2: 각 단계(분류, Neo4j 검색, ES 검색, SQL 조회)의 결과를 출력
- 7.3: 적용된 필터 조건과 제외된 매물 수를 표시
- 7.4: 매물 상세 정보와 점수를 포맷팅하여 표시

Usage:
    python scripts/test_search_pipeline.py
    python scripts/test_search_pipeline.py --question "홍대 근처 원룸 추천해줘"
    python scripts/test_search_pipeline.py --verbose
"""

import os
import sys
import argparse
import time
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'apps', 'rag'))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(os.path.join(project_root, '.env'))


class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(text: str):
    """Print a formatted header"""
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}{text}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'='*60}{Colors.ENDC}\n")


def print_section(title: str):
    """Print a section title"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}▶ {title}{Colors.ENDC}")
    print(f"{Colors.CYAN}{'-'*50}{Colors.ENDC}")


def print_success(text: str):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.ENDC}")


def print_warning(text: str):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.ENDC}")


def print_error(text: str):
    """Print error message"""
    print(f"{Colors.RED}✗ {text}{Colors.ENDC}")


def print_info(text: str):
    """Print info message"""
    print(f"{Colors.BLUE}ℹ {text}{Colors.ENDC}")


def format_price(deposit: int, rent: int = 0, trade_type: str = '') -> str:
    """Format price for display (만원 단위)"""
    if trade_type == '매매':
        if deposit >= 10000:
            return f"매매 {deposit // 10000}억 {deposit % 10000}만원" if deposit % 10000 else f"매매 {deposit // 10000}억"
        return f"매매 {deposit}만원"
    elif trade_type == '전세':
        if deposit >= 10000:
            return f"전세 {deposit // 10000}억 {deposit % 10000}만원" if deposit % 10000 else f"전세 {deposit // 10000}억"
        return f"전세 {deposit}만원"
    else:
        return f"보증금 {deposit}만원 / 월세 {rent}만원"


def format_score(score: float) -> str:
    """Format score for display"""
    return f"{score:.2f}" if score else "N/A"


class SearchPipelineTester:
    """Terminal-based search pipeline tester"""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.graph = None
        self.stats = {
            'classify_time': 0,
            'neo4j_time': 0,
            'es_time': 0,
            'sql_time': 0,
            'generate_time': 0,
            'total_time': 0,
            'neo4j_count': 0,
            'es_count': 0,
            'sql_count': 0,
            'filtered_count': 0,
            'final_count': 0
        }
    
    def initialize(self):
        """Initialize the RAG graph"""
        print_section("Initializing RAG Pipeline")
        
        try:
            from graphs.listing_rag_graph import create_rag_graph
            self.graph = create_rag_graph()
            print_success("RAG graph initialized successfully")
            return True
        except Exception as e:
            print_error(f"Failed to initialize RAG graph: {e}")
            return False
    
    def run_search(self, question: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Run the full search pipeline
        
        Requirements 7.1: 사용자 질문을 입력받아 전체 검색 파이프라인을 실행
        """
        import uuid
        
        if not self.graph:
            if not self.initialize():
                return {}
        
        session_id = session_id or str(uuid.uuid4())
        
        print_header(f"Search Pipeline Test")
        print(f"{Colors.BOLD}Question:{Colors.ENDC} {question}")
        print(f"{Colors.BOLD}Session:{Colors.ENDC} {session_id[:8]}...")
        print(f"{Colors.BOLD}Time:{Colors.ENDC} {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        start_time = time.time()
        
        try:
            # Run the graph synchronously for terminal testing
            import asyncio
            
            async def run_async():
                return await self.graph.ainvoke({
                    "question": question,
                    "session_id": session_id,
                    "cached_property_ids": [],
                    "accumulated_results": {}
                })
            
            result = asyncio.run(run_async())
            
            self.stats['total_time'] = time.time() - start_time
            
            return result
            
        except Exception as e:
            print_error(f"Search failed: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    def display_results(self, result: Dict[str, Any]):
        """
        Display search results with detailed formatting
        
        Requirements 7.2: 각 단계의 결과를 출력
        Requirements 7.4: 매물 상세 정보와 점수를 포맷팅하여 표시
        """
        if not result:
            print_warning("No results to display")
            return
        
        # Display graph results (Neo4j + ES reranked)
        graph_results = result.get('graph_results', [])
        sql_results = result.get('sql_results', [])
        es_scores = result.get('es_scores', {})
        
        print_section("Search Results Summary")
        print(f"  Neo4j/ES Results: {len(graph_results)}")
        print(f"  SQL Results: {len(sql_results)}")
        print(f"  ES Scores Available: {len(es_scores)}")
        print(f"  Total Time: {self.stats['total_time']:.2f}s")
        
        # Display pipeline stages (Requirements 7.2)
        display_pipeline_stages(result, self.verbose)
        
        # Display ES scores if available
        if es_scores and self.verbose:
            print_section("ES Scores (Top 10)")
            sorted_scores = sorted(es_scores.items(), key=lambda x: x[1], reverse=True)[:10]
            for prop_id, score in sorted_scores:
                print(f"  {prop_id}: {format_score(score)}")
        
        # Display detailed property information
        if sql_results:
            self._display_property_details(sql_results, graph_results, es_scores)
        
        # Display final answer
        answer = result.get('answer', '')
        if answer:
            print_section("Generated Answer")
            print(answer)
    
    def _display_property_details(
        self, 
        sql_results: List[Dict], 
        graph_results: List[Dict],
        es_scores: Dict[str, float]
    ):
        """
        Display detailed property information
        
        Requirements 7.4: 매물 상세 정보와 점수를 포맷팅하여 표시
        """
        print_section(f"Property Details (Top {min(5, len(sql_results))})")
        
        # Create lookup for graph results
        graph_lookup = {}
        for r in graph_results:
            prop_id = str(r.get('id') or r.get('p.id', ''))
            if prop_id:
                graph_lookup[prop_id] = r
        
        for i, prop in enumerate(sql_results[:5], 1):
            land_num = str(prop.get('land_num', ''))
            
            print(f"\n{Colors.BOLD}{Colors.GREEN}[{i}] Property: {land_num}{Colors.ENDC}")
            print(f"  {Colors.CYAN}Address:{Colors.ENDC} {prop.get('address', 'N/A')}")
            print(f"  {Colors.CYAN}Type:{Colors.ENDC} {prop.get('building_type', 'N/A')}")
            
            # Price information
            trade_type = prop.get('parsed_trade_type', '')
            deposit = prop.get('parsed_deposit', 0)
            rent = prop.get('parsed_rent', 0)
            print(f"  {Colors.CYAN}Price:{Colors.ENDC} {format_price(deposit, rent, trade_type)}")
            
            # Scores
            graph_data = graph_lookup.get(land_num, {})
            neo4j_score = graph_data.get('total_score', 0)
            combined_score = graph_data.get('combined_score', 0)
            es_score = es_scores.get(land_num, 0)
            
            print(f"  {Colors.CYAN}Scores:{Colors.ENDC}")
            print(f"    Neo4j: {format_score(neo4j_score)}")
            print(f"    ES: {format_score(es_score)}")
            print(f"    Combined: {format_score(combined_score)}")
            
            # Infrastructure details from graph results
            if graph_data:
                poi_details = graph_data.get('poi_details', [])
                if poi_details:
                    poi_str = ', '.join([
                        f"{d.get('name', '')} ({d.get('dist', 0)}m)"
                        for d in poi_details if isinstance(d, dict)
                    ])
                    print(f"  {Colors.CYAN}POI:{Colors.ENDC} {poi_str}")
                
                # Safety info
                cctv_count = graph_data.get('cctv_count', 0)
                bell_count = graph_data.get('bell_count', 0)
                if cctv_count or bell_count:
                    print(f"  {Colors.CYAN}Safety:{Colors.ENDC} CCTV {cctv_count}개, 비상벨 {bell_count}개")
            
            # URL
            url = prop.get('url', '')
            if url:
                print(f"  {Colors.CYAN}URL:{Colors.ENDC} {url}")


def display_filter_details(question: str, sql_results: List[Dict], original_count: int):
    """
    Display filtering details
    
    Requirements 7.3: 적용된 필터 조건과 제외된 매물 수를 표시
    """
    from nodes.sql_search_node import extract_price_conditions
    
    print_section("Filter Analysis")
    
    # Extract price conditions
    price_conditions = extract_price_conditions(question)
    
    if price_conditions:
        print(f"  {Colors.BOLD}Applied Filters:{Colors.ENDC}")
        for key, value in price_conditions.items():
            if key == 'include_short_term':
                print(f"    - 단기임대 포함: {'예' if value else '아니오'}")
            elif key == 'trade_type_filter':
                print(f"    - 거래유형: {value}")
            elif 'deposit' in key:
                print(f"    - 보증금 {'이하' if 'max' in key else '이상'}: {value}만원")
            elif 'rent' in key:
                print(f"    - 월세 {'이하' if 'max' in key else '이상'}: {value}만원")
            elif 'jeonse' in key:
                print(f"    - 전세 {'이하' if 'max' in key else '이상'}: {value}만원")
            elif 'sale' in key:
                print(f"    - 매매가 {'이하' if 'max' in key else '이상'}: {value}만원")
    else:
        print(f"  {Colors.YELLOW}No price filters detected{Colors.ENDC}")
    
    # Display filtering statistics
    filtered_count = original_count - len(sql_results)
    print(f"\n  {Colors.BOLD}Filtering Statistics:{Colors.ENDC}")
    print(f"    - Original count: {original_count}")
    print(f"    - After filtering: {len(sql_results)}")
    print(f"    - Excluded: {filtered_count}")
    
    if filtered_count > 0:
        print(f"    - Exclusion rate: {filtered_count / original_count * 100:.1f}%")


def display_detailed_filter_breakdown(
    sql_results: List[Dict],
    price_conditions: Dict[str, Any]
):
    """
    Display detailed breakdown of filtered results by trade type and price range
    
    Requirements 7.3, 7.4: 필터링 결과 상세 출력
    """
    print_section("Detailed Filter Breakdown")
    
    if not sql_results:
        print_warning("No results to analyze")
        return
    
    # Group by trade type
    trade_type_groups: Dict[str, List[Dict]] = {}
    for prop in sql_results:
        trade_type = prop.get('parsed_trade_type', '기타')
        if trade_type not in trade_type_groups:
            trade_type_groups[trade_type] = []
        trade_type_groups[trade_type].append(prop)
    
    print(f"  {Colors.BOLD}Results by Trade Type:{Colors.ENDC}")
    for trade_type, props in sorted(trade_type_groups.items()):
        print(f"    - {trade_type}: {len(props)}개")
    
    # Price distribution analysis
    print(f"\n  {Colors.BOLD}Price Distribution:{Colors.ENDC}")
    
    deposits = [p.get('parsed_deposit', 0) for p in sql_results if p.get('parsed_deposit')]
    rents = [p.get('parsed_rent', 0) for p in sql_results if p.get('parsed_rent')]
    
    if deposits:
        min_dep = min(deposits)
        max_dep = max(deposits)
        avg_dep = sum(deposits) / len(deposits)
        print(f"    보증금: {min_dep}만원 ~ {max_dep}만원 (평균: {avg_dep:.0f}만원)")
    
    if rents:
        min_rent = min(rents)
        max_rent = max(rents)
        avg_rent = sum(rents) / len(rents)
        print(f"    월세: {min_rent}만원 ~ {max_rent}만원 (평균: {avg_rent:.0f}만원)")
    
    # Building type distribution
    building_types: Dict[str, int] = {}
    for prop in sql_results:
        btype = prop.get('building_type', '기타')
        building_types[btype] = building_types.get(btype, 0) + 1
    
    print(f"\n  {Colors.BOLD}Results by Building Type:{Colors.ENDC}")
    for btype, count in sorted(building_types.items(), key=lambda x: -x[1]):
        print(f"    - {btype}: {count}개")
    
    # Filter condition match analysis
    if price_conditions:
        print(f"\n  {Colors.BOLD}Filter Condition Match Analysis:{Colors.ENDC}")
        
        # Check how many results are at the boundary of filters
        deposit_max = price_conditions.get('deposit_max')
        rent_max = price_conditions.get('rent_max')
        
        if deposit_max:
            boundary_count = sum(
                1 for p in sql_results 
                if p.get('parsed_deposit', 0) >= deposit_max * 0.9
            )
            print(f"    - 보증금 상한 근처 (90%+): {boundary_count}개")
        
        if rent_max:
            boundary_count = sum(
                1 for p in sql_results 
                if p.get('parsed_rent', 0) >= rent_max * 0.9
            )
            print(f"    - 월세 상한 근처 (90%+): {boundary_count}개")


def display_pipeline_stages(result: Dict[str, Any], verbose: bool = False):
    """
    Display detailed information about each pipeline stage
    
    Requirements 7.2: 각 단계(분류, Neo4j 검색, ES 검색, SQL 조회)의 결과를 출력
    """
    print_section("Pipeline Stage Analysis")
    
    # Stage 1: Classification
    query_type = result.get('query_type', 'unknown')
    print(f"  {Colors.BOLD}1. Classification:{Colors.ENDC}")
    print(f"     Query Type: {query_type}")
    
    # Stage 2: Neo4j Search
    graph_results = result.get('graph_results', [])
    print(f"\n  {Colors.BOLD}2. Neo4j Search:{Colors.ENDC}")
    print(f"     Results: {len(graph_results)}")
    
    if graph_results and verbose:
        # Show sample of Neo4j results
        print(f"     Sample IDs: {[r.get('id') or r.get('p.id') for r in graph_results[:5]]}")
        
        # Show score distribution
        scores = [r.get('total_score', 0) for r in graph_results if r.get('total_score')]
        if scores:
            print(f"     Score Range: {min(scores):.0f} ~ {max(scores):.0f}")
    
    # Stage 3: ES Reranking
    es_scores = result.get('es_scores', {})
    print(f"\n  {Colors.BOLD}3. ES Reranking:{Colors.ENDC}")
    print(f"     ES Scores: {len(es_scores)}")
    
    if es_scores and verbose:
        sorted_scores = sorted(es_scores.values(), reverse=True)
        if sorted_scores:
            print(f"     Score Range: {sorted_scores[-1]:.2f} ~ {sorted_scores[0]:.2f}")
    
    # Check for combined scores
    combined_count = sum(1 for r in graph_results if r.get('combined_score'))
    if combined_count:
        print(f"     Combined Scores: {combined_count}")
    
    # Stage 4: SQL Search
    sql_results = result.get('sql_results', [])
    print(f"\n  {Colors.BOLD}4. SQL Search:{Colors.ENDC}")
    print(f"     Results: {len(sql_results)}")
    
    if sql_results and verbose:
        # Show sample addresses
        addresses = [r.get('address', '')[:30] for r in sql_results[:3]]
        for addr in addresses:
            print(f"       - {addr}...")
    
    # Stage 5: Generate
    answer = result.get('answer', '')
    print(f"\n  {Colors.BOLD}5. Generate:{Colors.ENDC}")
    print(f"     Answer Length: {len(answer)} chars")
    
    # Full results for caching
    full_results = result.get('full_results', [])
    if full_results:
        print(f"     Full Results (for cache): {len(full_results)}")


def interactive_mode(tester: SearchPipelineTester):
    """Run in interactive mode"""
    print_header("Interactive Search Pipeline Tester")
    print("Enter your search queries. Type 'quit' or 'exit' to stop.\n")
    
    session_id = None
    
    while True:
        try:
            question = input(f"{Colors.BOLD}Query> {Colors.ENDC}").strip()
            
            if not question:
                continue
            
            if question.lower() in ['quit', 'exit', 'q']:
                print_info("Goodbye!")
                break
            
            if question.lower() == 'new':
                session_id = None
                print_info("Started new session")
                continue
            
            if question.lower() == 'help':
                print_info("Commands:")
                print("  new   - Start a new session")
                print("  quit  - Exit the program")
                print("  help  - Show this help")
                continue
            
            # Run search
            result = tester.run_search(question, session_id)
            
            if result:
                # Update session_id for follow-up queries
                if not session_id:
                    import uuid
                    session_id = str(uuid.uuid4())
                
                # Display results
                tester.display_results(result)
                
                # Display filter details (Requirements 7.3)
                graph_results = result.get('graph_results', [])
                sql_results = result.get('sql_results', [])
                if graph_results:
                    display_filter_details(question, sql_results, len(graph_results))
                    
                    # Display detailed filter breakdown (Requirements 7.3, 7.4)
                    from nodes.sql_search_node import extract_price_conditions
                    price_conditions = extract_price_conditions(question)
                    display_detailed_filter_breakdown(sql_results, price_conditions)
            
            print()
            
        except KeyboardInterrupt:
            print_info("\nInterrupted. Goodbye!")
            break
        except Exception as e:
            print_error(f"Error: {e}")
            import traceback
            traceback.print_exc()


def main():
    parser = argparse.ArgumentParser(
        description='Terminal-based search pipeline tester',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/test_search_pipeline.py
  python scripts/test_search_pipeline.py --question "홍대 근처 원룸 추천해줘"
  python scripts/test_search_pipeline.py --question "보증금 5000만원 이하 월세 50만원 이하" --verbose
        """
    )
    
    parser.add_argument(
        '--question', '-q',
        type=str,
        help='Search question to test'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    parser.add_argument(
        '--session', '-s',
        type=str,
        help='Session ID for follow-up queries'
    )
    
    args = parser.parse_args()
    
    tester = SearchPipelineTester(verbose=args.verbose)
    
    if args.question:
        # Single query mode
        result = tester.run_search(args.question, args.session)
        if result:
            tester.display_results(result)
            
            # Display filter details (Requirements 7.3)
            graph_results = result.get('graph_results', [])
            sql_results = result.get('sql_results', [])
            if graph_results:
                display_filter_details(args.question, sql_results, len(graph_results))
                
                # Display detailed filter breakdown (Requirements 7.3, 7.4)
                from nodes.sql_search_node import extract_price_conditions
                price_conditions = extract_price_conditions(args.question)
                display_detailed_filter_breakdown(sql_results, price_conditions)
    else:
        # Interactive mode
        interactive_mode(tester)


if __name__ == '__main__':
    main()
