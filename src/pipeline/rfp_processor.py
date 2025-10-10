import asyncio
import time
from pathlib import Path
from typing import Dict, Any
import os
import sys

from tenacity import retry, stop_after_attempt, wait_exponential

# Add parent directory to path to import existing modules
sys.path.append(str(Path(__file__).parent.parent))


from ..llm_extractor.llm_extract_boq import extract_boq_criteria
from ..llm_extractor.llm_extract_pq import extract_prequalification_criteria  
from ..llm_extractor.llm_extract_pure_tq import extract_pure_technical_qualification
from ..llm_extractor.rfp_llm_summary import extract_rfp_key_details
from ..llm_extractor.llm_extract_payment_terms import extract_payment_terms
from .utils import convert_markdown_to_excel

class RFPProcessor:
    """Main processor for RFP pipeline"""
    
    def __init__(self):
        pass
    
    async def process_rfp(self, pdf_path: Path, session_folder: Path) -> Dict[str, Any]:
        """Process RFP through complete pipeline"""
        start_time = time.time()
        files_generated = []
        
        try:
            # Step 1: Parse PDF to Markdown
            print("🔄 Step 1: Parsing PDF to Markdown...")
            markdown_path = session_folder / "parsed" / "rfp.md"
            await self._parse_pdf_to_markdown(pdf_path, markdown_path)
            files_generated.append(str(markdown_path))
            
            # Read the parsed markdown content
            with open(markdown_path, 'r', encoding='utf-8') as f:
                rfp_content = f.read()
            
            # Step 2: Extract information using LLM modules
            print("🔄 Step 2: Extracting information using LLM modules...")
            
            # Import job manager for progress updates
            try:
                from ..job_manager import job_manager
                # Find job_id from session_folder path if available
                job_id = None
                for jid, job in job_manager.jobs.items():
                    if job.get('status') == 'processing':
                        job_id = jid
                        break
                if job_id:
                    job_manager.update_job(job_id, progress=30)
            except:
                pass
            
            extraction_tasks = [
                self._extract_boq(rfp_content, session_folder),
                self._extract_pq(rfp_content, session_folder), 
                self._extract_tq(rfp_content, session_folder),
                self._extract_summary(rfp_content, session_folder),
                self._extract_payment_terms(rfp_content, session_folder)
            ]
            
            extraction_results = await asyncio.gather(*extraction_tasks, return_exceptions=True)
            
            try:
                if job_id:
                    job_manager.update_job(job_id, progress=60)
            except:
                pass
            
            # Collect successful extractions
            for result in extraction_results:
                if isinstance(result, list):
                    files_generated.extend(result)
                elif isinstance(result, Exception):
                    print(f"⚠️ Extraction error: {result}")
            
            # Step 3: Convert markdown files to Excel
            print("🔄 Step 3: Converting to Excel format...")
            excel_tasks = [
                self._convert_specific_to_excel(session_folder / "extracted" / "boq.md", 
                                              session_folder / "excel" / "boq.xlsx", "boq"),
                self._convert_specific_to_excel(session_folder / "extracted" / "prequalification.md",
                                               session_folder / "excel" / "prequalification.xlsx", "pq"),
                self._convert_specific_to_excel(session_folder / "extracted" / "technical_qualification.md",
                                               session_folder / "excel" / "technical_qualification.xlsx", "tq"),
                self._convert_specific_to_excel(session_folder / "extracted" / "summary.md",
                                               session_folder / "excel" / "summary.xlsx", "summary"),
                self._convert_specific_to_excel(session_folder / "extracted" / "payment_terms.md",
                                               session_folder / "excel" / "payment_terms.xlsx", "payment")
            ]
            
            excel_results = await asyncio.gather(*excel_tasks, return_exceptions=True)
            
            # Collect Excel files
            for result in excel_results:
                if isinstance(result, str):
                    files_generated.append(result)
                elif isinstance(result, Exception):
                    print(f"⚠️ Excel conversion error: {result}")
            
            processing_time = time.time() - start_time
            
            print(f"✅ Pipeline completed in {processing_time:.2f} seconds")
            print(f"📁 Generated {len(files_generated)} files")
            
            return {
                "files_generated": files_generated,
                "processing_time": processing_time
            }
            
        except Exception as e:
            print(f"❌ Pipeline error: {e}")
            raise e
    
    async def _parse_pdf_to_markdown(self, pdf_path: Path, output_path: Path):
        """Parse PDF using Docling without models"""
        def parse_sync():
            from docling.document_converter import DocumentConverter

            converter = DocumentConverter()
            result = converter.convert(str(pdf_path))
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(result.document.export_to_markdown())
            return str(output_path)
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, parse_sync)
    
    async def _extract_boq(self, rfp_content: str, session_folder: Path) -> list:
        """Extract Bill of Quantities"""
        def extract_sync():
            output_path = session_folder / "extracted" / "boq.md"
            success = extract_boq_criteria(rfp_content, str(output_path))
            return [str(output_path)] if success else []
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, extract_sync)
    
    async def _extract_pq(self, rfp_content: str, session_folder: Path) -> list:
        """Extract Prequalification criteria"""
        def extract_sync():
            output_path = session_folder / "extracted" / "prequalification.md"
            success = extract_prequalification_criteria(rfp_content, str(output_path))
            return [str(output_path)] if success else []
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, extract_sync)
    
    async def _extract_tq(self, rfp_content: str, session_folder: Path) -> list:
        """Extract Technical Qualification criteria"""
        def extract_sync():
            output_path = session_folder / "extracted" / "technical_qualification.md"
            success = extract_pure_technical_qualification(rfp_content, str(output_path))
            return [str(output_path)] if success else []
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, extract_sync)
    
    async def _extract_summary(self, rfp_content: str, session_folder: Path) -> list:
        """Extract RFP summary"""
        def extract_sync():
            output_path = session_folder / "extracted" / "summary.md"
            success = extract_rfp_key_details(rfp_content, str(output_path))
            return [str(output_path)] if success else []
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, extract_sync)
    
    async def _extract_payment_terms(self, rfp_content: str, session_folder: Path) -> list:
        """Extract Payment Terms"""
        def extract_sync():
            output_path = session_folder / "extracted" / "payment_terms.md"
            result = extract_payment_terms(rfp_content, str(output_path))
            return [str(output_path)] if result else []
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, extract_sync)
    
    async def _convert_specific_to_excel(self, markdown_path: Path, excel_path: Path, converter_type: str) -> str:
        """Convert markdown to Excel using specific converters"""
        def convert_sync():
            if not markdown_path.exists():
                return None
            
            try:
                if converter_type == "boq":
                    from ..excel_convertor.boq_to_excel import create_boq_excel
                    create_boq_excel(str(markdown_path), str(excel_path))
                elif converter_type == "pq":
                    from ..excel_convertor.pq_to_excel import create_prequalification_excel
                    create_prequalification_excel(str(markdown_path), str(excel_path))
                elif converter_type == "tq":
                    from ..excel_convertor.pure_tq_to_excel import create_tq_excel
                    create_tq_excel(str(markdown_path), str(excel_path))
                elif converter_type == "summary":
                    from ..excel_convertor.rfp_summary_to_excel import create_rfp_excel
                    create_rfp_excel(str(markdown_path), str(excel_path))
                elif converter_type == "payment":
                    from ..excel_convertor.payment_terms_to_excel import create_payment_terms_excel
                    create_payment_terms_excel(str(markdown_path), str(excel_path))
                else:
                    # Use utils converter as fallback
                    from .utils import convert_markdown_to_excel
                    with open(markdown_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    convert_markdown_to_excel(content, excel_path, "Data")
                
                return str(excel_path)
            except Exception as e:
                print(f"Excel conversion error for {converter_type}: {e}")
                return None
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, convert_sync)